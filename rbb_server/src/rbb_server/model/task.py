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

import base64
import hashlib

from rbb_server.helper.permissions import hide, has_permission, Permissions
from sqlalchemy import *

from rbb_swagger_server.models.task_detailed import TaskDetailed
from rbb_swagger_server.models.task_summary import TaskSummary
from .base import Base


class TaskState(Enum):
    Queued = 0
    Running = 1
    Paused = 2
    Finished = 100
    Cancelled = 101
    CancellationRequested = 102


class Task(Base):
    __tablename__ = "task_queue"
    uid = Column(Integer, primary_key=True)
    priority = Column(Integer)
    description = Column(String(200))
    assigned_to = Column(String(100))
    created = Column(DateTime, server_default="now() AT TIME ZONE 'utc'")
    last_updated = Column(DateTime, server_default="now() AT TIME ZONE 'utc'")
    state = Column(Integer)
    task = Column(String(100))
    configuration = Column(JSON)
    result = Column(JSON)
    success = Column(Boolean)
    runtime = Column(Float)
    log = Column(Text)
    worker_labels = Column(String(255))
    task_hash = Column(String(50))

    @staticmethod
    def calculate_hash(config):
        m = hashlib.md5()
        m.update(repr(config).encode())
        return base64.b64encode(m.digest()).decode('latin-1')

    @staticmethod
    def task_assignment_query(session, uid, worker_name):
        result = session.execute("UPDATE task_queue "
                               "SET assigned_to=:assigned_to, state=1 "
                                "WHERE uid=:uid AND assigned_to=''",
                               {'uid': uid, 'assigned_to': worker_name})
        return result.rowcount == 1

    @staticmethod
    def task_prio_up(session, uid):
        result = session.execute("UPDATE task_queue "
                               "SET priority=x.new_prio FROM (SELECT max(priority) + 1 as new_prio FROM task_queue) x "
                                "WHERE uid=:uid",
                               {'uid': uid })

    def to_swagger_model_summary(self, model=None, user=None):
        if model is None:
            model = TaskSummary()

        model.detail_type = "TaskSummary"
        model.identifier = str(self.uid)
        model.priority = self.priority
        model.description = self.description
        model.assigned_to = self.assigned_to
        model.created = self.created
        model.last_updated = self.last_updated
        model.state = self.state
        model.task = self.task
        model.success = self.success
        model.runtime = self.runtime if self.runtime else 0
        model.worker_labels = self.worker_labels
        return model

    def to_swagger_model_detailed(self, user=None):
        model = self.to_swagger_model_summary(TaskDetailed(), user=user)  # type: TaskDetailed
        model.detail_type = "TaskDetailed"
        model.config = self.configuration
        model.result = hide(self.result, user, Permissions.QueueResultAccess, {"_hidden": True})
        model.log = hide(self.log, user, Permissions.QueueResultAccess, "_hidden")

        return model

    def from_swagger_model(self, api_model, user=None):
        model = api_model  # type: TaskDetailed

        self.configuration = model.config

        if has_permission(user, Permissions.QueueResultAccess):
            self.result = model.result
            self.log = model.log

        self.priority = model.priority
        self.description = model.description
        self.assigned_to = model.assigned_to
        self.created = model.created.replace(tzinfo=None)
        self.last_updated = model.last_updated.replace(tzinfo=None)
        self.state = model.state
        self.task = model.task
        self.success = model.success
        self.runtime = model.runtime
        self.worker_labels = model.worker_labels

        return self
