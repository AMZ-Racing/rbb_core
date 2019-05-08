# AMZ-Driverless
#  Copyright (c) 2019 Authors:
#   - Huub Hendrikx <hhendrik@ethz.ch>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import datetime
import importlib
import logging
import os
import sys
import time
import traceback
from Queue import Empty
from multiprocessing import Process, Queue

from rbb_client.apis.basic_api import BasicApi
from rbb_client.models import TaskDetailed
from rbb_tools.common.shell import stream_redirected

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class TaskNotFoundException(RuntimeError):
    pass


class TaskNotAllowedException(RuntimeError):
    pass


class OutSplitter():

    def __init__(self, original_out, combined_buffer):
        self.combined_buffer = combined_buffer
        self.original_out = original_out

    def write(self, s):
        self.original_out.write(s)
        self.combined_buffer.write(s)

    def flush(self):
        self.original_out.flush()
        self.combined_buffer.flush()


def get_task(api, name):
    initial_timeout = 5
    max_timeout = 600
    timeout = initial_timeout
    repeat = True
    task = None
    code = None

    while repeat:
        try:
            task = api.dequeue_task(name, "", "")  # type: TaskDetailed
            code = api.api_client.last_response.status
            repeat = False
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            logging.exception("Exception while getting task from server")
            logging.warning("Retrying after %d seconds...", timeout)
            time.sleep(timeout)
            timeout = timeout * initial_timeout
            timeout = min(timeout, max_timeout)

    return task, code


def work(api, name, poll_timeout):
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting to do work as '%s'." % name)
    api = api   # type: BasicApi

    config_registry = api.get_configuration_key("worker.default")
    task_update_interval = int(config_registry['worker']['default']['update_interval'])

    running = True
    while running:
        try:
            task, code = get_task(api, name)

            if task and code != 204:
                spawn_and_monitor_subtask(task, api, update_interval=task_update_interval)
            else:
                time.sleep(poll_timeout)

            # Exit after current task is finished
            if os.path.isfile("./rbbtools-stop"):
                logging.info("Stopping.")
                running = False

        except KeyboardInterrupt:
            running = False
            print("Exiting.")
        except Exception as e:
            running = False
            logging.exception("Exception in main loop")


def spawn_and_monitor_subtask(task, api, update_interval=20):
    logging.info("Starting task '%s' with id '%s'..." % (task.task, task.identifier))
    q = Queue()
    p = Process(target=task_process, args=(api, task, q))

    # Remove old output stream
    if os.path.exists("child_out.log"):
        os.unlink("child_out.log")

    # Register starting time and start process
    start_time = time.time()
    p.start()
    logging.info("Started task with PID %d" % p.pid)

    # Wait for process entry point to run
    while not os.path.exists("child_out.log"):
        logging.info("Waiting for task output stream to become available...")
        time.sleep(0.1)

    logging.info("Stream available!")

    # Open the log
    log_file = open("child_out.log", 'r')
    log_buffer = ""

    # Monitor cancellation status and periodically upload logs
    cancelled = False
    result = None
    running = True
    while running:
        try:
            # TODO: Read timeout from system settings registry
            result = q.get(timeout=update_interval)
            running = False
        except Empty as e:
            log_buffer += log_file.read()

            # If writing log to server succeeds we can clear the buffer because we are appending
            if append_log_to_task(api, task, log_buffer):
                log_buffer = ""

            # Check if the task is cancelled
            if check_task_cancelled(api, task):
                cancelled = True
                running = False
                p.terminate()

    # Wait for process to end
    log_file.close()
    p.join()

    # We still upload the log completely, to have a complete correct version
    with open("child_out.log", 'r') as f:
        log = f.read()
    print("Log received on main node")

    if cancelled:
        log += "\n\n TASK WAS CANCELLED\n"

    duration = time.time() - start_time
    exit_code = p.exitcode
    mark_task_as_done(api, task, result, log, exit_code, duration, cancelled)

    logging.info("Finished task '%s' with code %d." % (task.identifier, exit_code))


def append_log_to_task(api, task, log_append):
    task_patch = {
        'log_append': log_append
    }

    try:
        api.patch_task(task.identifier, task_patch)
        return True
    except Exception as e:
        logging.exception("Exception while saving task")
        return False


def check_task_cancelled(api, task):
    try:
        task = api.get_task(task.identifier)

        if task.state >= 100:
            return True

        return False
    except Exception as e:
        logging.exception("Exception while getting task state")
        return False


def mark_task_as_done(api, task, result, log, exit_code, duration, cancelled):
    task.log = log
    task.state = 101 if cancelled else 100  # Finished
    task.runtime = duration
    task.last_updated = datetime.datetime.utcnow()

    if exit_code == 0:
        task.success = True
        if isinstance(result, dict):
            task.result = result
        else:
            task.result = {
                'result': result
            }
    else:
        task.success = False
        task.result = {
            "exit_code": exit_code,
        }

    retries = 3
    initial_timeout = 10
    timeout = 10
    while retries > 0:
        retries -= 1

        try:
            api.put_task(task.identifier, task)
        except Exception as e:
            if retries == 0:
                raise e
            logging.exception("Exception while saving task")
            logging.warning("Retrying after %d seconds...", timeout)
            time.sleep(timeout)
            timeout = timeout * initial_timeout


def task_process(api, task, queue):
    result = None
    with open("child_out.log", 'w') as child_out, \
            stream_redirected(child_out, sys.stdout), \
            stream_redirected(child_out, sys.stderr):
        try:
            result = run_task(api, task)
        except Exception as e:
            # Make sure the traceback appears in the captured stderr
            traceback.print_exc(file=sys.stderr)
            # This will cause a non zero exit code and maybe other wanted effects
            raise e
        finally:
            queue.put(result)


def run_task(api, task):
    module_parts = task.task.split(".")

    for part in module_parts:
        if part.strip() == "":
            raise TaskNotAllowedException()

    # This should be made configurable, but for now we only allow tasks that are part of rbb_tools.tasks
    if ".".join(module_parts[:-2]) != "rbb_tools.tasks":
        raise TaskNotAllowedException()

    try:
        plugin = importlib.import_module(".".join(module_parts[:-1]))
    except ImportError as e:
        logging.exception("Import of task module failed")
        raise TaskNotFoundException()

    f = getattr(plugin, module_parts[-1])

    return f(task.config, api)
