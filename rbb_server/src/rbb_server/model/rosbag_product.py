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

from sqlalchemy import *
from sqlalchemy.orm import relationship

from rbb_swagger_server.models import Product, TopicMapping, ProductFile
from .base import Base
from .file import File
from .rosbag_product_file import RosbagProductFile
from .rosbag_product_topic import RosbagProductTopic


class RosbagProduct(Base):
    __tablename__ = "rosbag_product"
    uid = Column(Integer, primary_key=True)
    bag_id = Column(Integer, ForeignKey('rosbag.uid'))
    plugin = Column(String(100))
    product_type = Column(String(100))
    product_data = Column(JSON)
    created = Column(DateTime, server_default="now() AT TIME ZONE 'utc'")
    title = Column(String(200))
    configuration_tag = Column(String(100))
    configuration_rule = Column(String(100))

    # Relationship
    bag = relationship("Rosbag", back_populates="products")
    topics = relationship("RosbagProductTopic", cascade="all, delete-orphan")
    files = relationship("RosbagProductFile", cascade="all, delete-orphan")

    def to_swagger_model_detailed(self):
        model = Product (
            uid=self.uid,
            plugin=self.plugin,
            product_type=self.product_type,
            product_data=self.product_data,
            created=self.created,
            title=self.title,
            configuration_tag=self.configuration_tag,
            configuration_rule=self.configuration_rule
        )

        model.topics = []
        for t in self.topics:
            model.topics.append(TopicMapping(
                original_topic=t.topic.name,
                plugin_topic=t.plugin_topic
            ))

        model.files = []
        for f in self.files:
            model.files.append(ProductFile(
                key=f.key,
                file=f.file.to_swagger_model_summary()
            ))

        return model

    def from_swagger_model(self, api_model):
        model = api_model  # type: Product
        self.plugin = model.plugin
        self.product_data = model.product_data
        self.product_type = model.product_type
        self.created = model.created.replace(tzinfo=None)
        self.title = model.title
        self.configuration_tag = model.configuration_tag
        self.configuration_rule = model.configuration_rule
        return self

    def topic_mapping_from_swagger_model(self, api_model, topics):
        model = api_model  # type: Product

        self.topics = []

        for topic_mapping in model.topics:
            topic = list(filter(lambda x: x.name == topic_mapping.original_topic, topics))

            if len(topic) == 0:
                raise ValueError("Topic %s not in topics" % topic_mapping.original_topic)
            else:
                self.topics.append(RosbagProductTopic(
                    plugin_topic = topic_mapping.plugin_topic,
                    topic = topic[0],
                ))

        return self

    def file_mapping_from_swagger_model(self, api_model, session):
        model = api_model  # type: Product

        self.files = []
        for file_link in model.files: # type: ProductFile
            file = session.query(File).get(file_link.file.uid)

            if not file or file.name != file_link.file.name:
                raise ValueError("File %d (%s) not found" % (file_link.file.uid, file_link.file.name))
            else:
                self.files.append(RosbagProductFile(
                    key = file_link.key,
                    file = file
                ))

        return self

