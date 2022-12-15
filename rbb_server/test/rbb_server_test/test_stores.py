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

from rbb_client import BagDetailed, TopicMapping, Topic, Product, FileSummary, ProductFile, BagStoreDetailed
from rbb_client.api_client import ApiException
from rbb_server_test import ClientServerBaseTestCase


class TestStores(ClientServerBaseTestCase):

    def test_list_stores(self):
        api = self.get_api()
        stores = api.list_stores()
        self.assertIsNotNone(stores)

    def test_create_store(self):
        api = self.get_api()

        store = BagStoreDetailed()
        store.detail_type = "BagStoreDetailed"
        store.name = "test-store-creation"
        store.description = "some description"
        store.default_file_store = ''
        store.created = datetime.datetime.utcnow()
        store.store_type = "rbb_storage_static"
        store.store_data = {
            'static': {}
        }

        return_store = api.put_store(store.name, store)

        self.assertEquals(return_store.name, store.name)
        self.assertEquals(return_store.description, store.description)
        self.assertEquals(return_store.default_file_store, store.default_file_store)
        self.assertEquals(return_store.created, store.created.replace(tzinfo=return_store.created.tzinfo))
        self.assertEquals(return_store.store_type, store.store_type)
        self.assertEquals(return_store.store_data, store.store_data)

    def test_edit_store(self):
        api = self.get_api()

        store = BagStoreDetailed()
        store.detail_type = "BagStoreDetailed"
        store.name = "test-store-edit"
        store.description = "some description"
        store.default_file_store = ''
        store.created = datetime.datetime.utcnow()
        store.store_type = "rbb_storage_static"
        store.store_data = {
            'static': {}
        }

        return_store = api.put_store(store.name, store)

        store.description = "Changed"
        store.store_type = "rbb_storage_s3"
        store.store_data = {
            's3': {}
        }

        return_store = api.put_store(store.name, store)

        self.assertEquals(return_store.name, store.name)
        self.assertEquals(return_store.description, store.description)
        self.assertEquals(return_store.default_file_store, store.default_file_store)
        self.assertEquals(return_store.created, store.created.replace(tzinfo=return_store.created.tzinfo))
        self.assertEquals(return_store.store_type, store.store_type)
        self.assertEquals(return_store.store_data, store.store_data)

    def test_delete_full_store(self):
        api = self.get_api()

        store = BagStoreDetailed()
        store.detail_type = "BagStoreDetailed"
        store.name = "test-store-deletion"
        store.description = "some description"
        store.default_file_store = ''
        store.created = datetime.datetime.utcnow()
        store.store_type = "rbb_storage_static"
        store.store_data = {
            'static': {}
        }
        return_store = api.put_store(store.name, store)

        bag = BagDetailed()
        bag.detail_type="BagDetailed"
        bag.name="some-bag.bag"
        bag.store_data={}
        bag.is_extracted=True
        bag.meta_available=True
        bag.discovered=datetime.datetime.now(datetime.timezone.utc)
        bag.size=1234567
        bag.start_time=datetime.datetime.fromtimestamp(1514456400, datetime.timezone.utc)
        bag.end_time=datetime.datetime.fromtimestamp(1514456497, datetime.timezone.utc)
        bag.duration=90.5
        bag.messages=10000
        bag.comment="Very nice bag"

        topic1 = Topic()
        topic1.name="/pointcloud"
        topic1.msg_type="sensor_msgs/Pointcloud2"
        topic1.msg_type_hash="Some hash"
        topic1.msg_definition="Some definition"
        topic1.msg_count=10000
        topic1.avg_frequency=1000
        bag.topics=[topic1]

        tm = TopicMapping()
        tm.plugin_topic="p"
        tm.original_topic = "/pointcloud"

        file_summary = FileSummary()
        file_summary.detail_type = "FileSummary"
        file_summary.uid = 2
        file_summary.name = "video.mp4"
        file_summary.store_name = "google-cloud"
        file_summary.link = ""

        pf = ProductFile()
        pf.file = file_summary
        pf.key = "video"

        product1 = Product()
        product1.uid=""
        product1.plugin = "Test"
        product1.product_type = "Movie"
        product1.product_data = {}
        product1.title = "Lalala"
        product1.configuration_rule = "rule1"
        product1.configuration_tag = "config-file"
        product1.created = datetime.datetime.now(datetime.timezone.utc)
        product1.topics = [tm]
        product1.files = [pf]
        bag.products = [product1]

        response_bag = self.get_api().put_bag_meta(store.name, bag.name, bag)  # type: rbb_client.BagDetailed

        api.delete_store(store.name)

        # Check it's gone
        try:
            return_bag = api.get_bag_meta(store.name, bag.name)
            self.fail("Bag not found exception should be thrown")
        except ApiException as e:
            self.assertEquals(e.status, 404)

        # Check it's gone
        try:
            return_store = api.get_store(store.name)
            self.fail("Store not found exception should be thrown")
        except ApiException as e:
            self.assertEquals(e.status, 404)

    def test_delete_empty_store(self):
        api = self.get_api()

        store = BagStoreDetailed()
        store.detail_type = "BagStoreDetailed"
        store.name = "test-store-deletion-full"
        store.description = "some description"
        store.default_file_store = ''
        store.created = datetime.datetime.utcnow()
        store.store_type = "rbb_storage_static"
        store.store_data = {
            'static': {}
        }

        return_store = api.put_store(store.name, store)
        api.delete_store(store.name)

        # Check it's gone
        try:
            return_store = api.get_store(store.name)
            self.fail("Store not found exception should be thrown")
        except ApiException as e:
            self.assertEquals(e.status, 404)

    def test_create_new_bag(self):
        bag = BagDetailed()
        bag.detail_type="BagDetailed"
        bag.name="unittest.bag"
        bag.store_data={'s3': {'uuid': 23094, 'path': '/test/test/test'}}
        bag.is_extracted=True
        bag.meta_available=True
        bag.discovered=datetime.datetime.now(datetime.timezone.utc)
        bag.size=1234567
        bag.start_time=datetime.datetime.fromtimestamp(1514456400, datetime.timezone.utc)
        bag.end_time=datetime.datetime.fromtimestamp(1514456497, datetime.timezone.utc)
        bag.duration=90.5
        bag.messages=10000
        bag.comment="Very nice bag"

        topic1 = Topic()
        topic1.name="/pointcloud"
        topic1.msg_type="sensor_msgs/Pointcloud2"
        topic1.msg_type_hash="Some hash"
        topic1.msg_definition="Some definition"
        topic1.msg_count=10000
        topic1.avg_frequency=1000
        bag.topics=[topic1]

        tm = TopicMapping()
        tm.plugin_topic="p"
        tm.original_topic = "/pointcloud"

        file_summary = FileSummary()
        file_summary.detail_type = "FileSummary"
        file_summary.uid = 2
        file_summary.name = "video.mp4"
        file_summary.store_name = "google-cloud"
        file_summary.link = ""

        pf = ProductFile()
        pf.file = file_summary
        pf.key = "video"

        product1 = Product()
        product1.uid=""
        product1.plugin = "Test"
        product1.product_type = "Movie"
        product1.product_data = {}
        product1.title = "Lalala"
        product1.configuration_rule = "rule1"
        product1.configuration_tag = "config-file"
        product1.created = datetime.datetime.now(datetime.timezone.utc)
        product1.topics = [tm]
        product1.files = [pf]
        bag.products = [product1]

        response_bag = self.get_api().put_bag_meta('test', bag.name, bag)  # type: rbb_client.BagDetailed
        self.assertBagEqual(bag, response_bag)
        self.assertTopicEqual(bag.topics[0], response_bag.topics[0])
        self.assertEqual(len(bag.products), len(response_bag.products))
        self.assertProductEqual(bag.products[0], response_bag.products[0])









