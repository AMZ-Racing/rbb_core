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

import time
import unittest
from multiprocessing import Process

import urllib.request

import rbb_client
import test_server


class ClientServerBaseTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._server_app = test_server.construct_test_server()

        def run_server():
            cls._server_app.run(host='localhost', port=8081, threaded=False)

        cls._server = Process(target=run_server)
        cls._server.start()

        if not cls.wait_for_server():
            cls.tearDownClass()
            raise RuntimeError("Timeout while waiting for Flask server to start!")


    @classmethod
    def wait_for_server(cls):
        retries = 10
        while retries > 0:
            try:
                test = urllib.request.urlopen("http://localhost:8081/api/v0").read()
                return True
            except urllib.request.URLError as e:
                if isinstance(e, urllib.request.HTTPError):
                    return True

            time.sleep(0.05)
            retries -= 1

        return False


    @classmethod
    def tearDownClass(cls):
        cls._server.terminate()
        cls._server.join()

    def get_admin_api(self):
        return self.get_api("admin", "admin")

    def get_user_api(self):
        return self.get_api("user", "user")

    def get_api(self, api_username="admin", api_password="admin", api_key=""):
        if api_key != "":
            rbb_client.configuration.use_bearer_auth = True
            rbb_client.configuration.token = api_key
        else:
            rbb_client.configuration.use_bearer_auth = False
            rbb_client.configuration.username = api_username
            rbb_client.configuration.password = api_password

        api_instance = rbb_client.BasicApi(rbb_client.ApiClient(host="http://localhost:8081/api/v0"))
        return api_instance

    def assertBagEqual(self, bag, response_bag):
        self.assertEqual(bag.name, response_bag.name)
        self.assertEqual(bag.store_data, response_bag.store_data)
        self.assertEqual(bag.is_extracted, response_bag.is_extracted)
        self.assertEqual(bag.meta_available, response_bag.meta_available)
        self.assertLessEqual((bag.discovered - response_bag.discovered).total_seconds(), 1)
        self.assertEqual(bag.size, response_bag.size)
        self.assertLessEqual((bag.start_time - response_bag.start_time).total_seconds(), 1)
        self.assertLessEqual((bag.end_time - response_bag.end_time).total_seconds(), 1)
        self.assertEqual(bag.duration, response_bag.duration)
        self.assertEqual(bag.messages, response_bag.messages)

    def assertTopicEqual(self, topic, response_topic):
        self.assertEqual(topic.name, response_topic.name)
        self.assertEqual(topic.msg_type, response_topic.msg_type)
        self.assertEqual(topic.msg_type_hash, response_topic.msg_type_hash)
        self.assertEqual(topic.msg_definition, response_topic.msg_definition)
        self.assertEqual(topic.msg_count, response_topic.msg_count)
        self.assertEqual(topic.avg_frequency, response_topic.avg_frequency)

    def assertProductEqual(self, product, response_product):
        self.assertEqual(product.plugin, response_product.plugin)
        self.assertEqual(product.product_type, response_product.product_type)
        self.assertEqual(product.product_data, response_product.product_data)
        self.assertLessEqual((product.created - response_product.created).total_seconds(), 1)
        topic_map = lambda x: x.original_topic + "-" + x.plugin_topic
        self.assertSetEqual(set(map(topic_map, product.topics)), set(map(topic_map, response_product.topics)))
        product_map = lambda x: x.key + "-" + x.file.store_name + "-" + x.file.name
        self.assertSetEqual(set(map(product_map, product.files)), set(map(product_map, response_product.files)))