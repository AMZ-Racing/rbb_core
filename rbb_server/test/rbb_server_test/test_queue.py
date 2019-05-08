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
import unittest
import multiprocessing
import time

from sqlalchemy.orm import Query

import rbb_server_test.database
from rbb_server.controllers.queue_controller import dequeue_task_inner, put_task_inner
from rbb_server.model.database import Database, Task, User
from rbb_swagger_server.models.task_detailed import TaskDetailed


class TestQueue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rbb_server_test.database.setup_database_for_test()

    @classmethod
    def tearDownClass(cls):
        if Database.get_session():
            Database.get_session().remove()

    def test_deque_under_load(self):
        fill_start_time = time.time()
        number_of_processes = max(2, multiprocessing.cpu_count())
        number_of_queued_items = 2000 * number_of_processes

        Database.get_session().execute('''TRUNCATE TABLE task_queue CASCADE''')
        Database.get_session().commit()

        # Fill queue
        for i in range(number_of_queued_items):
            task = Task()
            task.priority = 0
            task.description = "T%d" % i
            task.assigned_to = ""
            task.created = datetime.datetime.now()
            task.last_updated = datetime.datetime.now()
            task.state = 0
            task.task = "none"
            task.success = False
            task.result = {}
            task.runtime = 0
            task.worker_labels = ""
            task.configuration = {}
            Database.get_session().add(task)

        Database.get_session().commit()

        admin_user = Database.get_session().query(User).filter(User.alias == 'admin').first()

        rbb_server_test.database.close_database()

        fill_end_time = time.time()
        dequeue_start_time = time.time()

        # Start dequeuing processes
        processes = []

        def run(q, worker_name):
            rbb_server_test.database.init_database_connection_for_test()

            tasks = []
            number_of_collisions = 0
            while True:
                task = dequeue_task_inner(worker_name, "", "", admin_user)

                if isinstance(task, TaskDetailed):
                    tasks.append(task.description)
                    task.state = 100
                    put_task_inner(task.identifier, task, admin_user)
                else:
                    # Check if the queue is empty, if not then there was a collision
                    count = Database.get_engine().execute('''select count(uid) from task_queue where assigned_to='' ''').scalar()

                    if count > 0:
                        number_of_collisions += 1
                    else:
                        rbb_server_test.database.close_database()
                        q.put((tasks, number_of_collisions))
                        return

        for i in range(number_of_processes):
            queue = multiprocessing.Queue()
            process = multiprocessing.Process(target=run, args=(queue, "w%d" % i) )
            process.start()
            processes.append((process, queue))

        dequeued_tasks = []
        tasks_per_process = []
        total_number_of_collisions = 0
        for i in range(number_of_processes):
            process, queue = processes[i]
            process.join()
            tasks_dequeued, number_of_collisions = queue.get()
            tasks_per_process.append(len(tasks_dequeued))
            dequeued_tasks.extend(tasks_dequeued)
            total_number_of_collisions += number_of_collisions

        dequeue_end_time = time.time()

        print("Filling the database took %f seconds" % (fill_end_time - fill_start_time))
        print("Dequeueing took %f seconds (%f per task)" %
              (dequeue_end_time - dequeue_start_time, (dequeue_end_time - dequeue_start_time) / number_of_queued_items))
        print("Number of tasks dequeued per process: ", tasks_per_process)
        print("Number of collisions: ", total_number_of_collisions)


        self.assertEqual(len(dequeued_tasks), number_of_queued_items)



