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

import datetime

from rbb_client.api_client import ApiException
from rbb_client.models import FileStore
from rbb_server_test import ClientServerBaseTestCase


class TestFileStorage(ClientServerBaseTestCase):

    def test_new_file_store(self):
        api = self.get_admin_api()

        s = FileStore()
        s.name = "test-new"
        s.store_data = {}
        s.store_type = "rbb_storage_mock"
        s.created = datetime.datetime.now()

        sim = api.put_file_store(s.name, s)
        sim_result = api.get_file_store(s.name)

        self.assertEqual(sim.name, sim_result.name)
        self.assertEqual(sim.store_data, sim_result.store_data)
        self.assertEqual(sim.store_type, sim_result.store_type)
        self.assertEqual(sim.created, sim_result.created)

    def test_delete_file_store(self):
        api = self.get_admin_api()

        sim = api.get_file_store("delete-file-store")
        api.delete_file_store("delete-file-store")
        try:
            sim = api.get_file_store("delete-file-store")
            self.fail("Exception should be thrown")
        except ApiException as e:
            self.assertEqual(e.status, 404)








