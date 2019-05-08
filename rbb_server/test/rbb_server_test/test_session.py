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

import rbb_client
from rbb_server_test import ClientServerBaseTestCase


class TestSession(ClientServerBaseTestCase):

    def test_no_access(self):
        api_instance = self.get_api()
        rbb_client.configuration.username = ''
        rbb_client.configuration.password = ''

        with self.assertRaises(rbb_client.api_client.ApiException) as context:
            api_instance.list_stores()

        self.assertEqual(context.exception.status, 401)

    def test_session(self):
        api = self.get_api()
        session = api.new_session()

        rbb_client.configuration.username = ''
        rbb_client.configuration.password = ''
        rbb_client.configuration.use_bearer_auth = True
        rbb_client.configuration.token = session.token

        stores = api.list_stores()

        self.assertTrue(isinstance(stores, list))

    def test_session_only_password(self):
        api = self.get_api()
        session = api.new_session()

        rbb_client.configuration.username = ''
        rbb_client.configuration.password = ''
        rbb_client.configuration.use_bearer_auth = True
        rbb_client.configuration.token = session.token

        # Requesting a new session while authenticated with a session token should not be possible
        with self.assertRaises(rbb_client.api_client.ApiException) as context:
            api.new_session()

        self.assertEqual(context.exception.status, 401)

    def test_session_fake(self):
        api = self.get_api()
        rbb_client.configuration.username = ''
        rbb_client.configuration.password = ''
        rbb_client.configuration.use_bearer_auth = True
        rbb_client.configuration.token = "My1PYmZ0SHNwMjZEVksxeko0ZEdoc0dlS0R1RWQ5dHM5NlBQSi9mZDZydWVzPQ=="

        with self.assertRaises(rbb_client.api_client.ApiException) as context:
            api.list_stores()

        self.assertEqual(context.exception.status, 401)
