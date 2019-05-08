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
import logging
import random
import time
import urllib
from functools import wraps

from flask import request, Response
from werkzeug import http

import rbb_server.helper.permissions as permissions
from rbb_server.model.database import Database, User, Session


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    try:
        q = Database.get_session().query(User).filter(User.alias == username)
        if q.count():
            user = q.first()
            if user.check_password(password):
                return user

    except Exception as e:
        logging.exception(e)

    return False


def new_user_session(user, valid_for=3600):
    db_session = Database.get_session()
    user_session = Session(user=user, token=generate_random_secret(), valid_for=valid_for)
    db_session.add(user_session)
    db_session.commit()
    return user_session


def authenticate(browser_popup=True):
    """Sends a 401 response that enables basic auth"""
    logging.warning("Unauthorized request from %s to %s %s" % (request.remote_addr, request.method, request.path))
    return Response('Unauthorized.',
                    401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'} if browser_popup else {})


def missing_permission():
    logging.warning("Unauthorized request from %s to %s %s, missing permission" %
                    (request.remote_addr, request.method, request.path))
    return Response('Forbidden, missing permission.', 403)


def generate_random_secret():
    # TODO: Make the secret a config parameter
    secret = "I*YGF(*yu4tsoiefujwetaw45ey89e4w7r"
    string = "%f%f%s" % (random.random(), time.time(), secret)
    output = base64.b64encode(hashlib.sha256(string.encode('utf-8')).digest())
    return output.decode('latin-1')


def unpack_token(string):
    parts = string.split(b'-')
    if len(parts) is not 2:
        return None

    return {
        'id': int(parts[0]),
        'token': parts[1].decode('latin1')
    }


def get_current_session_id_and_token():
    auth_header = request.environ.get('HTTP_AUTHORIZATION')
    auth_token = ""

    if auth_header:
        value = http.wsgi_to_bytes(auth_header)
        try:
            auth_type, auth_token = value.split(None, 1)
            auth_type = auth_type.lower()

            if auth_type != b'bearer':
                return None

        except ValueError:
            logging.warning("Invalid Auth header")
            return None
    elif "rbbtoken" in request.cookies:
        # Session token in cookie needs to be supported for embedded media links
        auth_token = urllib.parse.unquote(request.cookies['rbbtoken']).encode('latin1')
    else:
        return None

    return unpack_token(base64.b64decode(auth_token))


def get_current_session():
    session_info = get_current_session_id_and_token()
    if not session_info:
        return None
    q = Database.get_session().query(Session).filter(Session.uid == session_info['id'])
    if q.count():
        session = q.first()
        if session.token == session_info['token']:
            return session

    return None


def requires_auth(only_username_password=False, keyword_arg='user'):
    def requires_auth_inner(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization

            # Username & password based authentication
            if auth:
                user = check_auth(auth.username, auth.password)
                if not user:
                    return authenticate(False)
                kwargs[keyword_arg] = user
                return f(*args, **kwargs)

            # Maybe token authentication
            elif not only_username_password:
                session = get_current_session()
                if session:
                    # TODO: Check expiry of auth token
                    kwargs[keyword_arg] = session.user
                    return f(*args, **kwargs)

            return authenticate()

        return decorated
    return requires_auth_inner


def requires_permission(permission, keyword_arg='user'):
    def requires_permission_inner(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Need to be logged in
            if keyword_arg not in kwargs:
                return authenticate()

            user = kwargs[keyword_arg]
            if permissions.has_permission(user, permission):
                return f(*args, **kwargs)

            return missing_permission()

        return decorated
    return requires_permission_inner


def requires_auth_with_permission(permission, keyword_arg='user'):
    def requires_auth_with_permission_inner(f):
        dec = requires_auth(keyword_arg=keyword_arg)(
            requires_permission(permission=permission, keyword_arg=keyword_arg)(f))
        return dec
    return requires_auth_with_permission_inner
