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
from datetime import datetime
from rbb_server.model.task import TaskState, Task


class NewBagHook():
    _hooks = []

    @classmethod
    def trigger(cls, new_bag, store_name, session, trigger=None, user=None):
        for hook in cls._hooks:
            new_bag = hook.trigger(new_bag, store_name, session, trigger, user)
        return new_bag

    @classmethod
    def register(cls):
        if cls != NewBagHook:
            if not hasattr(cls, "_registered"):
                cls._registered = True
                cls._hooks.append(cls)


class ScheduleBagExtractionOnNewBag(NewBagHook):

    @classmethod
    def trigger(cls, new_bag, store_name, session, trigger=None, user=None):
        task = Task()
        bag = new_bag  # type: Rosbag
        task.priority = 100
        task.description = "Extract discovered bag (%s/%s)" % (store_name, bag.name)
        task.assigned_to = ""
        task.created = datetime.utcnow()
        task.state = TaskState.Queued
        task.task = "rbb_tools.tasks.bags.extract"
        task.configuration = {
            'store': store_name,
            'configuration': 'auto',
            'bag': bag.name
        }
        task.result = {}
        task.success = False
        task.log = ""
        task.runtime = None
        task.worker_labels = ""
        task.task_hash = Task.calculate_hash(task.configuration)

        session.add(task)
        session.commit()

        return new_bag


ScheduleBagExtractionOnNewBag.register()


