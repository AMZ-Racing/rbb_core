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

from rbb_client.api_client import ApiException
from rbb_client.models import User
from rbb_server_test import ClientServerBaseTestCase


class TestUsers(ClientServerBaseTestCase):

    def test_get_me(self):
        api = self.get_admin_api()
        result = api.get_current_user()  # type: User
        self.assertEqual(result.alias, 'admin')

    def test_get_unknown_user(self):
        api = self.get_admin_api()
        try:
            returned_user = api.get_user_account("this-user-for-sure-doesnt-exist")
            self.fail("Exception should be thrown")
        except ApiException as e:
            self.assertEquals(e.status, 404)

    def test_get_user_no_permission(self):
        api = self.get_user_api()
        try:
            returned_user = api.get_user_account("admin")
            self.fail("Exception should be thrown")
        except ApiException as e:
            self.assertEquals(e.status, 403)

    def test_add_new_user(self):
        api = self.get_admin_api()

        user = User()
        user.alias = "test_user"
        user.email = "test@test.nl"
        user.full_name = "Test User"
        user.password = "testtest"

        returned_user = api.put_user_account(user.alias, user)

        self.assertEqual(user.alias, returned_user.alias)
        self.assertEqual(user.email, returned_user.email)
        self.assertEqual(user.full_name, returned_user.full_name)
        self.assertIsNone(returned_user.password)

        # Login as created user
        api = self.get_api("test_user", "testtest")
        fetched_user = api.get_current_user()

        # Check that data is the same
        self.assertEqual(user.alias, fetched_user.alias)
        self.assertEqual(user.email, fetched_user.email)
        self.assertEqual(user.full_name, fetched_user.full_name)
        self.assertIsNone(fetched_user.password)

    def test_change_user_permissions(self):
        api = self.get_admin_api()

        user = User()
        user.alias = "test_user_permissions"
        user.email = "test@test.nl"
        user.full_name = "Test User"
        user.password = "testtest"

        returned_user = api.put_user_account(user.alias, user)
        self.assertGreaterEqual(len(returned_user.permissions), 4)
        perm_dict = {}
        for perm in returned_user.permissions:
            perm_dict[perm.identifier] = perm
            self.assertFalse(perm.granted)

        perm_dict['admin'].granted = False
        perm_dict['queue_result_access'].granted = True

        api.put_user_account(returned_user.alias, returned_user)
        returned_user = api.get_user_account(user.alias)

        perm_dict = {}
        for perm in returned_user.permissions:
            perm_dict[perm.identifier] = perm

        self.assertFalse(perm_dict['admin'].granted)
        self.assertTrue(perm_dict['queue_result_access'].granted)
        self.assertFalse(perm_dict['store_secret_access'].granted)


    def test_add_new_user_no_permission(self):
        api = self.get_user_api()

        user = User()
        user.alias = "test_user"
        user.email = "test@test.nl"
        user.full_name = "Test User"
        user.password = "testtest"

        try:
            returned_user = api.put_user_account(user.alias, user)
            self.fail("Exception should be thrown")
        except ApiException as e:
            self.assertEquals(e.status, 403)

    def test_change_password(self):
        api = self.get_admin_api()

        user = User()
        user.alias = "test_user_password"
        user.email = "test@test.nl"
        user.full_name = "Test User"
        user.password = "testtest"
        api.put_user_account(user.alias, user)

        user_data = api.get_user_account(user.alias)
        user_data.password = "changed_password"
        api.put_user_account(user.alias, user_data)

        # Login as created user
        api = self.get_api("test_user_password", "changed_password")
        fetched_user = api.get_current_user()
        self.assertEquals(fetched_user.alias, user.alias)

    def test_delete_user(self):
        api = self.get_admin_api()

        user = User()
        user.alias = "to_delete"
        user.email = "test@test.nl"
        user.full_name = "Test User"
        user.password = "testtest"

        # Add user
        returned_user = api.put_user_account(user.alias, user)

        # Check it's there
        fetched_user = api.get_user_account(user.alias)
        self.assertEqual(user.alias, fetched_user.alias)

        # Delete
        api.delete_user_account(user.alias)

        # Check it's gone
        try:
            returned_user = api.get_user_account(user.alias)
            self.fail("User not found exception should be thrown")
        except ApiException as e:
            self.assertEquals(e.status, 404)


    def test_list_users(self):
        api = self.get_admin_api()
        accounts = api.list_user_accounts()
        self.assertGreater(len(accounts), 0)

        account_dict = {}
        for account in accounts:
            account_dict[account.alias] = account

        self.assertEquals(account_dict['admin'].full_name, 'Admin')
        self.assertEquals(account_dict['user'].full_name, 'User')








