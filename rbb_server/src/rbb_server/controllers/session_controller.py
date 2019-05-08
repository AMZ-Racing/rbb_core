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
import rbb_server.helper.error as error_helper
from rbb_server.helper.permissions import Permissions

from rbb_server.model.database import Database, Session
from rbb_swagger_server.models.error import Error


@auth.requires_auth(only_username_password=True)
def new_session(valid_for=None, user=None):
    """
    Create a new session


    :rtype: User
    """
    try:
        # Unless otherwise specified, sessions are valid for an hour
        if valid_for is None:
            valid_for = 3600

        return auth.new_user_session(user, valid_for).to_swagger_model(show_token=True)
    except Exception as e:
        return error_helper.handle_exception(e)


@auth.requires_auth()
def list_sessions(user=None):
    """
    List current session


    :rtype: List[Session]
    """
    try:
        q = Database.get_session().query(Session).filter(Session.user_uid == user.uid)

        models = []
        for session in q:
            model = session.to_swagger_model()
            model.token = ""
            models.append(model)

        return models

    except Exception as e:
        return error_helper.handle_exception(e)


@auth.requires_auth()
def delete_session(session_id, user=None):
    """
    Delete a session or sessions

    :param session_id: Session id or all or current
    :type session_id: str

    :rtype: None
    """
    try:
        to_delete = []
        if session_id == "current":
            pass
        elif session_id == "all":
            pass
        else:
            try:
                id = int(session_id)
            except:
                return Error(400, "Invalid session id"), 400

        for session in to_delete:
            pass

    except Exception as e:
        return error_helper.handle_exception(e)