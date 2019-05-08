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

import rbb_server.helper.auth as auth
import rbb_server.helper.permissions as permissions
import rbb_server.helper.error as error_helper

from rbb_server.helper.permissions import Permissions
from rbb_server.model.database import Database, ConfigKeyValue
from rbb_swagger_server.models.error import Error


@auth.requires_auth_with_permission(Permissions.SystemConfigurationRead)
def get_configuration_key(config_key, user=None):  # noqa: E501
    """Get configuration key

     # noqa: E501

    :param config_key: Configuration key to read
    :type config_key: str

    :rtype: str
    """
    session = Database.get_session()
    try:
        dictionary = ConfigKeyValue.get_config_dict(config_key, session)

        # Wipe out secure
        if not permissions.has_permission(user, permissions.Permissions.SystemConfigurationSecretAccess):
            del dictionary['secret']

        return dictionary, 200

    except Exception as e:
        session.rollback()
        return error_helper.handle_exception(e)


@auth.requires_auth_with_permission(Permissions.SystemConfigurationWrite)
def put_configuration_key(config_key, config_value, user=None):  # noqa: E501
    """Write configuration key

     # noqa: E501

    :param config_key: Configuration key to read
    :type config_key: str
    :param config_value: Configuration key value
    :type config_value: str

    :rtype: None
    """
    try:
        # TODO: Will be implemented later
        raise NotImplementedError()
    except Exception as e:
        return error_helper.handle_exception(e)
