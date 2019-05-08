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
from rbb_client.models import BagExtractionConfiguration
from rbb_server_test import ClientServerBaseTestCase


class TestExtractionConfigurations(ClientServerBaseTestCase):

    def test_list_extraction_configs(self):
        api = self.get_admin_api()
        configs = api.list_extraction_configurations()
        self.assertGreaterEqual(len(configs), 1)
        self.assertEqual(configs[0].name, "test-config")

    def test_get_extraction_config(self):
        api = self.get_admin_api()
        config = api.get_extraction_config("test-config")
        self.assertEqual(config.name, "test-config")
        self.assertEqual(config.type, "git")
        self.assertEqual(config.config, {"git":{"url":"https://github.com/hfchendrikx/rbb-visualizations.git","branch":"master","path":"rviz-test"}})

    def test_edit_extraction_config(self):
        api = self.get_admin_api()
        config = api.get_extraction_config("test-config-2")
        self.assertEqual(config.name, "test-config-2")
        config.type = "somethingelse"
        config.description = "some description"
        config.config = {"test":"test"}
        api.put_extraction_configuration(config.name, config)
        resulting_config = api.get_extraction_config("test-config-2")
        self.assertEqual(config.name, resulting_config.name)
        self.assertEqual(config.type, resulting_config.type)
        self.assertEqual(config.config, resulting_config.config)
        self.assertEqual(config.description, resulting_config.description)

    def test_link_configuration(self):
        api = self.get_admin_api()
        config = BagExtractionConfiguration()
        config.name = "linked-config"
        config.type = "somethingelse"
        config.description = "some description"
        config.config = {"test":"test"}
        api.put_extraction_configuration(config.name, config)
        linked_config_names = api.put_store_extraction_configs("test", [config.name])
        self.assertEqual(linked_config_names, [config.name])
        linked_configs = api.get_store_extraction_configs("test")
        self.assertEqual(config.name, linked_configs[0].name)
        self.assertEqual(config.type, linked_configs[0].type)
        self.assertEqual(config.config, linked_configs[0].config)
        self.assertEqual(config.description, linked_configs[0].description)

    def test_delete_linked_configuration(self):
        api = self.get_admin_api()
        config = BagExtractionConfiguration()
        config.name = "linked-config-to-delete"
        config.type = "somethingelse"
        config.description = "some description"
        config.config = {"test":"test"}
        api.put_extraction_configuration(config.name, config)
        linked_config_names = api.put_store_extraction_configs("test", [config.name])
        self.assertEqual(linked_config_names, [config.name])

        api.delete_extraction_configuration(config.name)
        try:
            returned_config = api.get_extraction_config(config.name)
            self.fail("Exception should be thrown")
        except ApiException as e:
            self.assertEqual(e.status, 404)

    def test_add_configuration(self):
        api = self.get_admin_api()
        config = BagExtractionConfiguration()
        config.name = "new-configuration"
        config.type = "somethingelse"
        config.description = "some description"
        config.config = {"test":"test"}
        api.put_extraction_configuration(config.name, config)
        resulting_config = api.get_extraction_config(config.name)
        self.assertEqual(config.name, resulting_config.name)
        self.assertEqual(config.type, resulting_config.type)
        self.assertEqual(config.config, resulting_config.config)
        self.assertEqual(config.description, resulting_config.description)












