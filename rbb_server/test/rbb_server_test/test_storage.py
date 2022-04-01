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
import unittest

from sqlalchemy.orm import Query

import rbb_server_test.database
from rbb_server.model.database import Database
from rbb_server.model.rosbag import Rosbag
from rbb_server.model.rosbag_product import RosbagProduct
from rbb_server.model.rosbag_store import RosbagStore
from rbb_server.model.rosbag_topic import RosbagTopic


class TestStorage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rbb_server_test.database.setup_database_for_test()

    @classmethod
    def tearDownClass(cls):
        Database.get_session().remove()

    def test_get_store(self):
        result = Database.get_session().query(RosbagStore) #type: Query
        self.assertEqual(result.count(), 3)

    def test_insert_store(self):
        test_store = RosbagStore(
            name="some-test-store",
            description="test",
            store_type="s3",
            store_data="{}"
        )
        Database.get_session().add(test_store)
        Database.get_session().flush()
        self.assertIsNotNone(test_store.uid, "UID assigned after flush/commit")
        Database.get_session().commit()

    def test_update_store(self):
        test_store = RosbagStore(
            name="some-test-store-update",
            description="test",
            store_type="s3",
            store_data="{}"
        )
        Database.get_session().add(test_store)
        Database.get_session().commit()

        # Clear cache
        Database.get_session().expire_all()

        result = Database.get_session().query(RosbagStore).get(test_store.uid)
        self.assertIsNotNone(result, "Reload model from database")
        self.assertEqual(result.description, "test")
        result.description = "updated"
        Database.get_session().commit()

        # Clear cache
        Database.get_session().expire_all()

        result = Database.get_session().query(RosbagStore).get(test_store.uid)
        self.assertEqual(result.description, "updated")

    def test_get_bags_with_relationship(self):
        test = Database.get_session().query(RosbagStore).get(1).bags
        self.assertEqual(len(test), 3)
        self.assertEqual(test[0].name, "empty.bag")

    def test_insert_bag(self):
        bag = Rosbag(
            store=Database.get_session().query(RosbagStore).get(1),
            store_data={'test':'est'},
            name="Testbag",
            is_extracted=False,
            meta_available=False,
            size=100,
            start_time=datetime.datetime.now(),
            end_time=datetime.datetime.now(),
            duration=10.4,
            messages=10000,
            comment="Lalalalala"
        )
        Database.get_session().add(bag)
        Database.get_session().flush()
        self.assertIsNotNone(bag.uid, "UID assigned after flush/commit")
        Database.get_session().commit()

        bag = Database.get_session().query(Rosbag).get(bag.uid)
        self.assertEqual(bag.store_data['test'], 'est')

    def test_get_bag_topics(self):
        bag = Database.get_session().query(Rosbag).get(1) # type: Rosbag

        self.assertEqual(len(bag.topics), 2)
        for topic in bag.topics: #type: RosbagTopic
            self.assertEqual(topic.name, "/camera1" if topic.uid == 1 else "/camera2")

    def test_get_bag_product_files(self):
        bag = Database.get_session().query(Rosbag).get(1) # type: Rosbag
        self.assertEqual(len(bag.products), 3)
        rviz_product = None
        for product in bag.products: #type: RosbagProduct
            if product.plugin == "RvizRecorder":
                rviz_product = product

        self.assertIsNotNone(rviz_product)
        self.assertEqual(len(rviz_product.files), 1)
        self.assertEqual(rviz_product.files[0].key, "video")
        self.assertEqual(rviz_product.files[0].file.name, "test.mp4")
        self.assertEqual(rviz_product.files[0].file.store.store_type, "google-cloud")




