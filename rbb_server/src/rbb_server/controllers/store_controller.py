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

import connexion

from rbb_server.helper.permissions import Permissions
from rbb_swagger_server.models.bag_store_detailed import BagStoreDetailed
from rbb_swagger_server.models.error import Error
from rbb_server.model.database import Database, RosbagStore, FileStore
from flask import current_app, url_for
from sqlalchemy.orm.query import Query
import logging
import rbb_server.helper.auth as auth
import rbb_storage
from rbb_server.helper.storage import Storage
from flask import request as flask_request
from sqlalchemy.orm.attributes import flag_modified

@auth.requires_auth_with_permission(Permissions.BagStoreRead)
def get_store(store_name, user=None):
    """
    Get store details
    
    :param store_name: Name of the store
    :type store_name: str

    :rtype: BagStoreDetailed
    """
    try:
        q = Database.get_session().query(RosbagStore).filter(RosbagStore.name == store_name) #type: Query
        if q.count():
            return q[0].to_swagger_model_detailed(user=user)
        else:
            return Error(code=404, message="Store not found"), 404

    except Exception as e:
        if current_app.config['TESTING']:
            return Error(code=500, message="Exception: " + str(e)), 500
        else:
            return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth_with_permission(Permissions.BagStoreRead)
def list_stores(user=None):
    """
    List available stores
    

    :rtype: List[BagStoreDetailed]
    """
    try:
        q = Database.get_session().query(RosbagStore)
        return [p.to_swagger_model_detailed(user=user) for p in q]
    except Exception as e:
        if current_app.config['TESTING']:
            return Error(code=500, message="Exception: " + str(e)), 500
        else:
            return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth_with_permission(Permissions.BagStoreWrite)
def put_store(store_name, store, block_on_existing=None, user=None):
    """
    Create/update store

    :param store_name: Name of the store
    :type store_name: str
    :param store: Store information
    :type store: dict | bytes

    :rtype: BagStoreDetailed
    """
    if connexion.request.is_json:
        store = BagStoreDetailed.from_dict(connexion.request.get_json())

    if store_name != store.name:
        return Error(code=400, message="URL and body store names don't match"), 400

    if not Storage.plugin_exists(store.store_type):
        return Error(code=400, message="Unknown store type"), 400

    session = Database.get_session()
    try:
        # Check the store
        q = session.query(RosbagStore).filter(RosbagStore.name == store_name)  # type: Query

        # Create new store or use existing
        store_model = None
        if q.count() == 1:
            # Existing store
            if block_on_existing:
                return Error(code=1000, message="Already exists."), 400

            store_model = q.first()
        else:
            store_model = RosbagStore()
            session.add(store_model)

        store_model.from_swagger_model(store, user=user)

        if store.default_file_store:
            default_file_store = session.query(FileStore).filter(FileStore.name == store.default_file_store).first()

            if not default_file_store:
                return Error(code=400, message="Cannot find default file store"), 400

            store_model.default_file_store = default_file_store
        else:
            store_model.default_file_store = None

        session.commit()

        q = session.query(RosbagStore).filter(RosbagStore.uid == store_model.uid)

        return q.first().to_swagger_model_detailed(user=user), 200

    except Exception as e:
        logging.exception("Store put failed")
        session.rollback()

    return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth_with_permission(Permissions.BagStoreWrite)
def bag_store_authorize_step_get(store_name, step, user=None):
    """
    Authorization step forwarded to storage plugin

    :param store_name: Name of the store
    :type store_name: str
    :param step: Step of the authorization procedure
    :type step: str

    :rtype: None
    """
    session = Database.get_session()
    try:
        q = session.query(RosbagStore).filter(RosbagStore.name == store_name)  # type: Query
        if q.count():
            store = q[0]
            storage_plugin = Storage.factory(store_name, store.store_type, store.store_data)

            link = url_for(
                "/api/v0.rbb_server_controllers_store_controller_bag_store_authorize_step_get",
                store_name=store_name,
                step="",
                _external=True
            )

            response = storage_plugin.authorize_get_step(step, flask_request, link)

            if storage_plugin.needs_saving():
                store.store_data = storage_plugin.get_data()
                flag_modified(store, 'store_data')
                Database.get_session().commit()

            return response

        return Error(code=404, message="Store not found"), 404

    except Exception as e:
        logging.exception(e)
        return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth_with_permission(Permissions.BagStoreWrite)
def bag_store_authorize_step_post(store_name, step, user=None):
    """
    Authorization step forwarded to storage plugin

    :param store_name: Name of the store
    :type store_name: str
    :param step: Step of the authorization procedure
    :type step: str

    :rtype: None
    """
    try:
        q = Database.get_session().query(RosbagStore).filter(RosbagStore.name == store_name)  # type: Query
        if q.count():
            store = q[0]
            storage_plugin = Storage.factory(store_name, store.store_type, store.store_data)

            link = url_for(
                "/api/v0.rbb_server_controllers_store_controller_bag_store_authorize_step_post",
                store_name=store_name,
                step="",
                _external=True
            )

            response = storage_plugin.authorize_post_step(step, flask_request, link)

            if storage_plugin.needs_saving():
                store.store_data = storage_plugin.get_data()
                flag_modified(store, 'store_data')
                Database.get_session().commit()

            return response

        return Error(code=404, message="Store not found"), 404

    except Exception as e:
        logging.exception(e)
        return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth_with_permission(Permissions.BagStoreWrite)
def delete_store(store_name, user=None):  # noqa: E501
    """Delete file store

     # noqa: E501

    :param store_name: Name of the store
    :type store_name: str

    :rtype: None
    """
    session = Database.get_session()
    try:
        # Check the store
        q = Database.get_session().query(RosbagStore).filter(RosbagStore.name == store_name)  # type: Query
        if q.count() == 1:
            session.delete(q.first())
            session.commit()
            return "", 204
        else:
            return Error(code=404, message="Store not found"), 404

    except Exception as e:
        logging.exception("User account deletion failed")
        session.rollback()

    return Error(code=500, message="Exception occurred"), 500