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

import logging
from enum import Enum
from rbb_swagger_server.models.permission import Permission
from rbb_server.model.permission import Permission as DbPermission


class Permissions(Enum):
    Administration = "admin"

    StoreSecretAccess = "store_secret_access"
    FileStoreRead = "file_store_read"
    FileStoreWrite = "file_store_write"
    BagStoreRead = "bag_store_read"
    BagStoreWrite = "bag_store_write"
    DataFileStoreRead = "datafile_store_read"
    DataFileStoreWrite = "datafile_store_write"

    ExtractionConfigRead = "extraction_config_read"
    ExtractionConfigWrite = "extraction_config_write"

    BagRead = "bag_read"
    BagWrite = "bag_write"
    BagCommentRead = "bag_comment_read"
    BagCommentWrite = "bag_comment_write"

    DataFileRead = "datafile_read"
    DataFileWrite = "datafile_write"
    DataFileCommentRead = "datafile_comment_read"
    DataFileCommentWrite = "datafile_comment_write"

    UsersRead = "users_read"
    UsersWrite = "users_write"

    QueueRead = "queue_read"
    QueueWrite = "queue_write"
    QueueResultAccess = "queue_result_access"

    SimulationEnvironmentRead = "simenv_read"
    SimulationEnvironmentWrite = "simenv_write"
    SimulationEnvironmentConfigurationAccess = "simenv_config_access"
    SimulationRead = "sim_read"
    SimulationWrite = "sim_write"

    SystemConfigurationRead = "config_read"
    SystemConfigurationWrite = "config_write"
    SystemConfigurationSecretAccess = "config_secret_access"


def has_permission(user, permission):
    if user is None:
        return False

    if user.is_admin:
        return True

    permission_id = permission if isinstance(permission, str) else permission.value
    for p in user.permissions:
        if p.uid == permission_id:
            return True

    return False


def hide(value, user, permission, hidden=""):
    if user is not None and has_permission(user, permission):
        return value
    else:
        return hidden


def list_permissions():
    if not hasattr(list_permissions, "permission_list"):
        import rbb_server.model.database as database
        q = database.Database.get_session().query(database.Permission)
        list_permissions.permission_list = [x.to_swagger_model() for x in q]

    return list_permissions.permission_list


def list_user_permissions(user):
    permissions = list_permissions()

    permission_kv = {}
    for permission in permissions:
        permission_kv[permission.identifier] = Permission(identifier=permission.identifier,
                                                          name=permission.name,
                                                          granted=False)
    if user.is_admin:
        for k in permission_kv:
            permission_kv[k].granted = True
    else:
        for p in user.permissions:
            permission_kv[p.uid].granted = True

    permission_kv[Permissions.Administration.value] = Permission(identifier=Permissions.Administration.value,
                               name="Administrator Access",
                               granted=user.is_admin)

    permission_list = list(permission_kv.values())
    permission_list.sort(key=lambda x: x.name)
    return permission_list


def update_user_permissions(user, swagger_permissions, db_session):
    q = db_session.query(DbPermission)
    db_permission_kv = {}
    for pdb in q:
        db_permission_kv[pdb.uid] = pdb

    user_permission_kv = {}
    for pdb in user.permissions:
        user_permission_kv[pdb.uid] = pdb

    for permission in swagger_permissions:
        if permission.identifier == Permissions.Administration.value:
            user.is_admin = permission.granted
        else:
            if permission.identifier not in db_permission_kv:
                raise RuntimeError("Unknown permission '%s'" % (permission.identifier))

            if (not permission.granted) and (permission.identifier in user_permission_kv):
                user.permissions.remove(user_permission_kv[permission.identifier])

            if permission.granted and not permission.identifier in user_permission_kv:
                user.permissions.append(db_permission_kv[permission.identifier])
