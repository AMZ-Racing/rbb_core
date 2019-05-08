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
from functools import reduce

import connexion
import rbb_server.helper.auth as auth
import rbb_server.helper.database as db_helper
from rbb_server.helper.permissions import Permissions
from rbb_server.helper.error import handle_exception
from sqlalchemy import or_
from sqlalchemy.orm import Query

from rbb_server import Database
from rbb_server.model.database import Task
from rbb_server.model.task import TaskState
from rbb_swagger_server.models.error import Error
from rbb_swagger_server.models.task_detailed import TaskDetailed


@auth.requires_auth_with_permission(Permissions.QueueWrite)
def do_task_action(task_identifier, action, task=None, user=None):  # noqa: E501
    """Perform an action on the task

     # noqa: E501

    :param task_identifier:
    :type task_identifier: str
    :param action: Action to perform (cancel/prio_up)
    :type action: str
    :param task: The task, required depending on the action
    :type task: dict | bytes

    :rtype: TaskDetailed
    """
    try:
        if connexion.request.is_json and task:
            task = TaskDetailed.from_dict(connexion.request.get_json())  # noqa: E501

        session = Database.get_session()
        q = session.query(Task).filter(Task.uid == int(task_identifier))  # type: Query
        model = q.first()  # type: Task
        if not model:
            return Error(code=404, message="Task not found"), 404

        if action == "cancel":
            if model.state == TaskState.Queued:
                model.state = TaskState.Cancelled
                model.last_updated = datetime.datetime.utcnow()
            session.commit()
            return model.to_swagger_model_detailed(user)
        elif action == "cancel_running":
            if model.state == TaskState.Running:
                model.state = TaskState.CancellationRequested
                model.last_updated = datetime.datetime.utcnow()
            session.commit()
            return model.to_swagger_model_detailed(user)
        elif action == "prio_up":
            Task.task_prio_up(session, model.uid)
            session.commit()
            q = session.query(Task).filter(Task.uid == int(task_identifier))
            return q.first().to_swagger_model_detailed(user)
        else:
            return Error(code=400, message="Unknown action"), 400

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.QueueWrite)
def put_task(task_identifier, task, user=None):
    try:
        if connexion.request.is_json:
            task = TaskDetailed.from_dict(connexion.request.get_json())  # type: TaskDetailed

        return put_task_inner(task_identifier, task, user)
    except Exception as e:
        return handle_exception(e)


def put_task_inner(task_identifier, task, user=None):
    """Update a task

     # noqa: E501

    :param task_identifier:
    :type task_identifier: str
    :param task: The task
    :type task: dict | bytes

    :rtype: TaskDetailed
    """
    session = Database.get_session()

    try:
        identifier = int(task_identifier)
    except ValueError:
        return Error(code=400, message="Invalid task identifier"), 400

    q = session.query(Task).filter(Task.uid == int(identifier))  # type: Query
    model = q.first()  # type: Task
    if model:
        model.from_swagger_model(task, user=user)
        session.commit()

        # Return a fresh copy from the DB
        q = session.query(Task).filter(Task.uid == model.uid)
        return q.first().to_swagger_model_detailed(user=user), 200
    else:
        return Error(code=404, message="Task not found"), 404


@auth.requires_auth_with_permission(Permissions.QueueWrite)
def patch_task(task_identifier, task, user=None):  # noqa: E501
    """Partial update of task (this only supports a few fields)

     # noqa: E501

    :param task_identifier:
    :type task_identifier: str
    :param task: Fields to update
    :type task:

    :rtype: TaskDetailed
    """
    session = Database.get_session()

    try:
        identifier = int(task_identifier)
    except ValueError:
        return Error(code=400, message="Invalid task identifier"), 400

    try:
        q = session.query(Task).filter(Task.uid == int(identifier))  # type: Query
        model = q.first()
        if model:
            changed = False

            if 'log_append' in task and isinstance(task['log_append'], str):
                model.log += task['log_append']
                changed = True

            if changed:
                session.commit()

            return model.to_swagger_model_detailed(user=user)

        else:
            return Error(code=404, message="Task not found"), 404

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.QueueRead)
def get_task(task_identifier, user=None):
    """Take a task from the queue

     # noqa: E501

    :param task_identifier:
    :type task_identifier: str

    :rtype: TaskDetailed
    """
    try:
        session = Database.get_session()

        try:
            identifier = int(task_identifier)
        except ValueError:
            return Error(code=400, message="Invalid task identifier"), 400

        q = session.query(Task).filter(Task.uid == int(identifier))  # type: Query
        model = q.first()
        if model:
            return model.to_swagger_model_detailed(user=user)
        else:
            return Error(code=404, message="Task not found"), 404

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.QueueWrite)
def new_task(task, user=None):
    """Create a new task

     # noqa: E501

    :param task: The task
    :type task: dict | bytes

    :rtype: TaskDetailed
    """
    try:
        if connexion.request.is_json:
            task = TaskDetailed.from_dict(connexion.request.get_json())  # type: TaskDetailed

        session = Database.get_session()
        hash = Task.calculate_hash(task.config)

        q = session.query(Task)\
            .filter(Task.state < TaskState.Finished)\
            .filter(Task.task == task.task)\
            .filter(Task.task_hash == hash)

        duplicate_task = q.first()
        if duplicate_task:
            return Error(code=409, message="Duplicate task, %d, queued" % duplicate_task.uid), 409

        model = Task()
        model.log = ""
        model.result = {}
        model.task_hash = hash
        model.from_swagger_model(task, user=user)
        model.uid = None
        session.add(model)
        session.commit()

        # Return a fresh copy from the DB
        q = session.query(Task).filter(Task.uid == model.uid)
        return q.first().to_swagger_model_detailed(user=user), 200

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.QueueRead)
def list_queue(limit=None, offset=None, ordering=None, running=None, finished=None, queued=None, user=None):
    """List task queue

     # noqa: E501


    :rtype: List[TaskSummary]
    """
    try:
        session = Database.get_session()
        q = session.query(Task) #type: Query

        filters = []

        if running:
            filters.append(Task.state == TaskState.Running)

        if finished:
            filters.append(or_(Task.state == TaskState.Cancelled,
                               Task.state == TaskState.Finished,
                               Task.state == TaskState.CancellationRequested))

        if queued:
            filters.append(or_(Task.state == TaskState.Queued,
                               Task.state == TaskState.Paused))

        if len(filters) > 0:
            q = q.filter(reduce((lambda x, y: or_(x, y)), filters))

        q = db_helper.query_pagination_ordering(q, offset, limit, ordering, {
            'priority': Task.priority,
            'identifier': Task.uid,
            'last_updated': Task.last_updated,
            'created': Task.created,
            'state': Task.state,
            'success': Task.success,
            'runtime': Task.runtime
        })

        return [p.to_swagger_model_summary(user=user) for p in q]

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.QueueWrite)
def dequeue_task(worker_name, tasks, labels, user=None):
    try:
        return dequeue_task_inner(worker_name, tasks, labels, user)
    except Exception as e:
        return handle_exception(e)


def dequeue_task_inner(worker_name, tasks, labels, user=None):
    """Take a task from the queue

     # noqa: E501

    :param worker_name: Name of the worker trying to acquire a task
    :type worker_name: str
    :param tasks: Tasks that the worker can do (any or a list of tasks)
    :type tasks: str
    :param labels: Labels the worker wants to do
    :type labels: str

    :rtype: TaskDetailed
    """
    session = Database.get_session()

    # First find already assigned not finished tasks
    q = session.query(Task)  # type: Query
    q = q.filter(Task.assigned_to == worker_name)\
        .filter(Task.state < TaskState.Finished)\
        .order_by(Task.priority.desc()).limit(1)

    if q.count():
        return q.first().to_swagger_model_detailed(user=user)

    # Get a list of all tasks that can be done by this worker
    q = session.query(Task)  # type: Query
    q = q.filter(Task.assigned_to == "")\
        .filter(Task.state == TaskState.Queued)\
        .order_by(Task.priority.desc()).limit(5)

    # TODO: Filter label and tasks
    possible_tasks = []
    for possible_task in q:
        possible_tasks.append(possible_task)

    for task in possible_tasks:
        success = Task.task_assignment_query(session, task.uid, worker_name)

        if success:
            session.commit()
            q = session.query(Task).filter(Task.uid == task.uid)
            return q.first().to_swagger_model_detailed(user=user)


    return Error(code=204, message="No tasks in the queue"), 204

