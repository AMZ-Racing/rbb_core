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

import connexion
import rbb_server.helper.auth as auth
from rbb_server.helper.permissions import Permissions
from flask import current_app, redirect, Response, url_for
from flask import request as flask_request
from sqlalchemy import and_
from sqlalchemy.orm.attributes import flag_modified

import rbb_storage
from rbb_server.helper.storage import Storage
from rbb_server.model.database import Database, FileStore, File
from rbb_swagger_server.models.error import Error
from rbb_swagger_server.models.file_detailed import FileDetailed
from rbb_swagger_server.models.file_store import FileStore as SwaggerFileStore


@auth.requires_auth()
def get_file(store_name, uid, file_name, no_redirect=None, user=None):
    """
    Get file
    
    :param store_name: Name of the store
    :type store_name: str
    :param uid: Unique identifier of the file
    :type uid: int
    :param file_name: Name of the file
    :type file_name: str

    :rtype: Binary
    """
    try:
        q = Database.get_session().query(File).filter(
            and_(FileStore.name == store_name, File.uid == uid))  # type: Query
        if q.count():
            file = q[0]
            if file.name == file_name:

                storage_plugin = Storage.factory(store_name, file.store.store_type, file.store.store_data)
                link = storage_plugin.download_link(file.store_data)

                if no_redirect:
                    return Response(link), 213
                else:
                    return redirect(link, code=302)


        return Error(code=404, message="Store or file not found"), 404

    except Exception as e:
        logging.exception(e)
        if current_app.config['TESTING']:
            return Error(code=500, message="Exception: " + repr(e)), 500
        else:
            return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth()
def get_file_meta(store_name, uid, file_name, user=None):
    """
    Get file meta data
    
    :param store_name: Name of the store
    :type store_name: str
    :param uid: Unique identifier of the file
    :type uid: int
    :param file_name: Name of the file
    :type file_name: str

    :rtype: FileDetailed
    """
    try:
        q = Database.get_session().query(File).filter(
            and_(FileStore.name == store_name, File.uid == uid))  # type: Query
        if q.count():
            file = q[0]
            if file.name == file_name:
                return file.to_swagger_model_detailed(user=user)

        return Error(code=404, message="Store or file not found"), 404

    except Exception as e:
        if current_app.config['TESTING']:
            return Error(code=500, message="Exception: " + str(e)), 500
        else:
            return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth_with_permission(Permissions.FileStoreRead)
def get_file_store(store_name, user=None):
    """
    Get store details
    
    :param store_name: Name of the store
    :type store_name: str

    :rtype: FileStore
    """

    try:
        q = Database.get_session().query(FileStore).filter(FileStore.name == store_name) #type: Query
        if q.count():
            return q[0].to_swagger_model(user=user)
        else:
            return Error(code=404, message="Store not found"), 404

    except Exception as e:
        if current_app.config['TESTING']:
            return Error(code=500, message="Exception: " + str(e)), 500
        else:
            return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth_with_permission(Permissions.FileStoreRead)
def list_file_stores(user=None):
    """
    List available file stores
    

    :rtype: List[FileStore]
    """
    try:
        q = Database.get_session().query(FileStore)
        return [p.to_swagger_model(user=user) for p in q]
    except Exception as e:
        if current_app.config['TESTING']:
            return Error(code=500, message="Exception: " + str(e)), 500
        else:
            return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth_with_permission(Permissions.FileStoreWrite)
def new_file(store_name, file, user=None):
    """
    Register new file
    
    :param store_name: Name of the store
    :type store_name: str
    :param file: The file metadata
    :type file: dict | bytes

    :rtype: FileDetailed
    """
    if connexion.request.is_json:
        file = FileDetailed.from_dict(connexion.request.get_json())

    try:
        session = Database.get_session()
        q = session.query(FileStore).filter(
            and_(FileStore.name == store_name))  # type: Query
        if q.count():
            store = q[0]
            file_model = File()
            file_model.from_swagger_model(file, user)
            file_model.store = store
            file_model.uid = None
            session.add(file_model)
            session.commit()

            q = session.query(File).filter(
                and_(File.uid == file_model.uid)
            )
            return q.first().to_swagger_model_detailed(user=user), 200

        else:
            return Error(code=404, message="Store not found"), 404

    except Exception as e:
        logging.exception(e)
        if current_app.config['TESTING']:
            return Error(code=500, message="Exception: " + repr(e)), 500
        else:
            return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth_with_permission(Permissions.FileStoreWrite)
def authorize_step_get(store_name, step, user=None):
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
        q = session.query(FileStore).filter(FileStore.name == store_name)  # type: Query
        if q.count():
            store = q[0]
            storage_plugin = Storage.factory(store_name, store.store_type, store.store_data)

            link = url_for(
                "/api/v0.rbb_server_controllers_file_controller_authorize_step_get",
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


@auth.requires_auth_with_permission(Permissions.FileStoreWrite)
def authorize_step_post(store_name, step, user=None):
    """
    Authorization step forwarded to storage plugin

    :param store_name: Name of the store
    :type store_name: str
    :param step: Step of the authorization procedure
    :type step: str

    :rtype: None
    """
    try:
        q = Database.get_session().query(FileStore).filter(FileStore.name == store_name)  # type: Query
        if q.count():
            store = q[0]
            storage_plugin = Storage.factory(store_name, store.store_type, store.store_data)

            link = url_for(
                "/api/v0.rbb_server_controllers_file_controller_authorize_step_post",
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


@auth.requires_auth_with_permission(Permissions.FileStoreWrite)
def put_file_store(store_name, store, block_on_existing=None, user=None):  # noqa: E501
    """Create/update store

     # noqa: E501

    :param store_name: Name of the store
    :type store_name: str
    :param store: Store information
    :type store: dict | bytes

    :rtype: FileStore
    """
    if connexion.request.is_json:
        store = SwaggerFileStore.from_dict(connexion.request.get_json())  # noqa: E501

    if store_name != store.name:
        return Error(code=400, message="URL and body names don't match"), 400

    session = Database.get_session()
    try:
        # Check the store
        q = session.query(FileStore).filter(FileStore.name == store_name)  # type: Query

        # Create new store or use existing
        model = None
        if q.first():
            # Existing store
            if block_on_existing:
                return Error(code=1000, message="Already exists."), 400

            model = q.first()
        else:
            model = FileStore()
            session.add(model)

        model.from_swagger_model(store, user=user)
        session.commit()

        q = session.query(FileStore).filter(FileStore.uid == model.uid)

        return q.first().to_swagger_model(user=user), 200
    except Exception as e:
        logging.exception("File store put failed")
        session.rollback()

    return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth_with_permission(Permissions.FileStoreWrite)
def delete_file_store(store_name, user=None):  # noqa: E501
    """Delete file store

     # noqa: E501

    :param store_name: Name of the store
    :type store_name: str

    :rtype: None
    """
    session = Database.get_session()
    try:
        # Check the store
        q = Database.get_session().query(FileStore).filter(FileStore.name == store_name)  # type: Query
        if q.first():
            session.delete(q.first())
            session.commit()
            return "", 204
        else:
            return Error(code=404, message="File store not found"), 404

    except Exception as e:
        logging.exception("File store deletion failed")
        session.rollback()

    return Error(code=500, message="Exception occurred"), 500
