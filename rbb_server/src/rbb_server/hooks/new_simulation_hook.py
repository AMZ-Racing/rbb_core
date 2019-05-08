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
from rbb_server.model.task import TaskState, Task


class NewSimulationHook():
    _hooks = []

    @classmethod
    def trigger(cls, new_sim, session, trigger=None, user=None):
        for hook in cls._hooks:
            new_sim = hook.trigger(new_sim, session, trigger, user)
        return new_sim

    @classmethod
    def register(cls):
        if cls != __class__:
            if not hasattr(cls, "_registered"):
                cls._registered = True
                cls._hooks.append(cls)


class ScheduleOnNewSimulation(NewSimulationHook):

    @classmethod
    def trigger(cls, new_sim, session, trigger=None, user=None):
        task = Task()
        task.priority = 1000
        task.description = "Simulate #%d '%s'" % (new_sim.uid, new_sim.description)
        task.assigned_to = ""
        task.created = datetime.datetime.utcnow()
        task.state = TaskState.Queued
        task.task = "rbb_tools.tasks.sim.simulate"
        task.configuration = {
            'simulation': new_sim.uid
        }
        task.result = {}
        task.success = False
        task.log = ""
        task.runtime = None
        task.worker_labels = ""
        task.task_hash = Task.calculate_hash(task.configuration)
        new_sim.task_in_queue = task
        session.add(task)
        session.commit()

        return new_sim


ScheduleOnNewSimulation.register()
