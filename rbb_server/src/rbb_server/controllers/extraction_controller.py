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
from rbb_swagger_server.models.bag_extraction_configuration import BagExtractionConfiguration
from rbb_swagger_server.models.error import Error
from rbb_server.model.database import Database, RosbagExtractionConfiguration, RosbagStore
from sqlalchemy.orm.query import Query
import logging
import rbb_server.helper.auth as auth
from flask import request as flask_request
from sqlalchemy.orm.attributes import flag_modified
from rbb_server.helper.error import handle_exception


@auth.requires_auth_with_permission(Permissions.ExtractionConfigRead)
def get_extraction_config(config_name, user=None):
    """Get configuration details

    :param config_name: Name of the configuration
    :type config_name: str

    :rtype: BagExtractionConfiguration
    """
    try:
        q = Database.get_session().query(RosbagExtractionConfiguration).\
            filter(RosbagExtractionConfiguration.name == config_name) #type: Query
        if q.count():
            return q[0].to_swagger_model(user=user)
        else:
            return Error(code=404, message="Configuration not found"), 404

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.ExtractionConfigRead)
def list_extraction_configurations(user=None):
    """List available configurations


    :rtype: List[BagExtractionConfiguration]
    """
    try:
        q = Database.get_session().query(RosbagExtractionConfiguration)
        return [p.to_swagger_model(user=user) for p in q]
    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.ExtractionConfigRead)
def get_store_extraction_configs(store_name, user=None):
    """Get list of auto extraction configs

    :param store_name: Name of the store
    :type store_name: str

    :rtype: List[BagExtractionConfiguration]
    """
    try:
        q = Database.get_session().query(RosbagStore).filter(RosbagStore.name == store_name) #type: Query
        if q.count():
            return [x.to_swagger_model(user=user) for x in q.first().auto_extraction_configs]
        else:
            return Error(code=404, message="Store not found"), 404

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.BagStoreWrite)
def put_store_extraction_configs(store_name, config_list, user=None):
    """Create/update store

    :param store_name: Name of the store
    :type store_name: str
    :param store: List of config names
    :type store: List[]

    :rtype: List[str]
    """
    session = Database.get_session()
    try:
        q = session.query(RosbagStore).filter(RosbagStore.name == store_name) #type: Query
        if q.first():
            store = q.first()

            # Load configurations
            config_dict = {}
            for config in config_list:
                if config not in config_dict:
                    q = session.query(RosbagExtractionConfiguration)\
                        .filter(RosbagExtractionConfiguration.name == config)
                    if not q.first():
                        return Error(code=404, message="Configuration '%s' not found" % config), 404
                    config_dict[config] = q.first()

             # Assign new configurations
            store.auto_extraction_configs = list(config_dict.values())
            session.commit()

            return [x.name for x in store.auto_extraction_configs]
        else:
            return Error(code=404, message="Store not found"), 404

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.ExtractionConfigWrite)
def put_extraction_configuration(config_name, configuration_obj, block_on_existing=None, user=None):
    """Create/update configuration

    :param config_name: Name of the configuration
    :type config_name: str
    :param configuration: Configuration information
    :type configuration: dict | bytes

    :rtype: BagExtractionConfiguration
    """
    if connexion.request.is_json:
        configuration_obj = BagExtractionConfiguration.from_dict(connexion.request.get_json())

    if config_name != configuration_obj.name:
        return Error(code=400, message="URL and body names don't match"), 400

    session = Database.get_session()
    try:
        # Check the store
        q = session.query(RosbagExtractionConfiguration).filter(RosbagExtractionConfiguration.name == config_name)  # type: Query

        # Create new store or use existing
        model = None
        if q.count() == 1:
            # Existing configuration
            if block_on_existing:
                return Error(code=1000, message="Already exists."), 400

            model = q.first()
        else:
            model = RosbagExtractionConfiguration()
            session.add(model)

        model.from_swagger_model(configuration_obj, user=user)
        session.commit()

        q = session.query(RosbagExtractionConfiguration).filter(RosbagExtractionConfiguration.uid == model.uid)

        return q.first().to_swagger_model(user=user), 200

    except Exception as e:
        session.rollback()
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.ExtractionConfigWrite)
def delete_extraction_configuration(config_name, user=None):  # noqa: E501
    """Delete extraction configuration

     # noqa: E501

    :param config_name: Name of the configuration
    :type config_name: str

    :rtype: None
    """
    session = Database.get_session()
    try:
        # Check the store
        q = session.query(RosbagExtractionConfiguration).filter(RosbagExtractionConfiguration.name == config_name)  # type: Query
        if q.count() == 1:
            session.delete(q.first())
            session.commit()
            return "", 204
        else:
            return Error(code=404, message="Extraction configuration not found"), 404

    except Exception as e:
        session.rollback()
        return handle_exception(e)