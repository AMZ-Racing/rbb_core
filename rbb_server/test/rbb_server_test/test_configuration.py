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
from rbb_client.api_client import ApiException
from rbb_server_test import ClientServerBaseTestCase


class TestConfiguration(ClientServerBaseTestCase):

    def test_read_all_admin(self):
        api_instance = self.get_admin_api()
        config = dict(api_instance.get_configuration_key("*"))

        self.assertDictEqual(config['secret']['dropbox'], {
            'app_key': "",
            'app_secret': ""
        })

        self.assertDictEqual(config['worker']['default'], {
            'poll_interval': '10',
            'update_interval': '20'
        })

    def test_read_all_user_no_perm(self):
        api_instance = self.get_user_api()

        try:
            config = api_instance.get_configuration_key("*")
            self.fail("Exception should be thrown")
        except ApiException as e:
            self.assertEquals(e.status, 403)

    def test_read_all_user(self):
        admin_api = self.get_admin_api()
        user = admin_api.get_user_account('user')

        for p in user.permissions:
            if p.identifier == "config_read":
                p.granted = True

        user.alias = "user_with_config_read_perm"
        user.password = "user"
        admin_api.put_user_account(user.alias, user)

        api_instance = self.get_api(user.alias, 'user')
        config = api_instance.get_configuration_key("*")

        self.assertDictEqual(dict(config), {
            'worker': {
                'default': {
                    'poll_interval': '10',
                    'update_interval': '20'
                }
            }
        })
