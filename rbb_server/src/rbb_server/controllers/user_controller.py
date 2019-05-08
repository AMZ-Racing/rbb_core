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
from rbb_server.helper.permissions import Permissions, list_user_permissions, update_user_permissions

from rbb_server.model.database import Database, User
from rbb_swagger_server.models import User as SwaggerUser, Error


@auth.requires_auth(keyword_arg="logged_in_user")
def put_current_user(user, logged_in_user=None):
    """
    Change current user information


    :rtype: User
    """
    if connexion.request.is_json:
        user = SwaggerUser.from_dict(connexion.request.get_json())

    if logged_in_user.alias != user.alias:
        return Error(code=400, message="Alias cannot be changed"), 400

    session = Database.get_session()
    try:
        logged_in_user.from_swagger_model(user, user=logged_in_user)

        # Users are not allowed to change their own permissions...
        # if user.permissions is not None:
        #     update_user_permissions(logged_in_user, user.permissions)

        session.commit()

        q = session.query(User).filter(User.uid == logged_in_user.uid)
        swagger_user = q.first().to_swagger_model(user=logged_in_user)
        swagger_user.permissions = list_user_permissions(q.first())
        return swagger_user, 200

    except Exception as e:
        logging.exception("Current user put failed")
        session.rollback()

    return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth()
def get_current_user(user=None):
    """
    Get current user information


    :rtype: User
    """

    swagger_user = user.to_swagger_model()
    swagger_user.permissions = list_user_permissions(user)
    return swagger_user, 200


@auth.requires_auth_with_permission(Permissions.UsersWrite)
def delete_user_account(alias, user=None):  # noqa: E501
    """Delete user account

     # noqa: E501

    :param alias: Alias of the user
    :type alias: str

    :rtype: None
    """
    session = Database.get_session()
    try:
        # Check the store
        q = session.query(User).filter(User.alias == alias)  # type: Query
        if q.count() == 1:
            session.delete(q.first())
            session.commit()
            return "", 204
        else:
            return Error(code=404, message="User not found"), 404

    except Exception as e:
        logging.exception("User account deletion failed")
        session.rollback()

    return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth_with_permission(Permissions.UsersRead, keyword_arg="logged_in_user")
def get_user_account(alias, logged_in_user=None):  # noqa: E501
    """Get user information

     # noqa: E501

    :param alias: Alias of the user
    :type alias: str

    :rtype: User
    """
    session = Database.get_session()
    try:
        # Check the store
        q = session.query(User).filter(User.alias == alias)  # type: Query
        if q.count() == 1:
            swagger_user = q.first().to_swagger_model(user=logged_in_user)
            swagger_user.permissions = list_user_permissions(q.first())
            return swagger_user, 200
        else:
            return Error(code=404, message="User not found"), 404

    except Exception as e:
        logging.exception("User account put failed")
        session.rollback()

    return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth_with_permission(Permissions.UsersWrite, keyword_arg="logged_in_user")
def put_user_account(alias, user, block_on_existing=None, logged_in_user=None):  # noqa: E501
    """Change user information

     # noqa: E501

    :param alias: Alias of the user
    :type alias: str
    :param user: The user information
    :type user: dict | bytes

    :rtype: User
    """
    if connexion.request.is_json:
        user = SwaggerUser.from_dict(connexion.request.get_json())

    if alias != user.alias:
        return Error(code=400, message="URL and body aliases don't match"), 400

    if len(user.alias) < 4:
        return Error(code=400, message="Minimum alias length is 4 characters"), 400

    session = Database.get_session()
    try:
        # Check the store
        q = session.query(User).filter(User.alias == alias)  # type: Query

        # Create new store or use existing
        user_model = None
        if q.count() == 1:
            # Existing user
            if block_on_existing:
                return Error(code=1000, message="Already exists."), 400

            user_model = q.first()
        else:
            user_model = User()
            session.add(user_model)

        user_model.from_swagger_model(user, user=logged_in_user)
        if user.permissions is not None:
            update_user_permissions(user_model, user.permissions, session)
        session.commit()

        q = session.query(User).filter(User.uid == user_model.uid)

        swagger_user = q.first().to_swagger_model(user=logged_in_user)
        swagger_user.permissions = list_user_permissions(q.first())
        return swagger_user, 200

    except Exception as e:
        logging.exception("User account put failed")
        session.rollback()

    return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth_with_permission(Permissions.UsersRead)
def list_user_accounts(user=None):  # noqa: E501
    """List user acounts

     # noqa: E501


    :rtype: List[User]
    """
    session = Database.get_session()
    try:
        # Check the store
        q = session.query(User)  # type: Query
        return [x.to_swagger_model(user=user) for x in q], 200

    except Exception as e:
        logging.exception("List user accounts")
        session.rollback()

    return Error(code=500, message="Exception occurred"), 500

