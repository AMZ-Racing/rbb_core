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

from rbb_server.helper.permissions import hide, has_permission, Permissions
from sqlalchemy import *
from sqlalchemy.orm import relationship

from rbb_swagger_server.models import BagSummary, BagDetailed
from .base import Base

tag_association_table = Table('rosbag_tags', Base.metadata,
    Column('bag_id', Integer, ForeignKey('rosbag.uid')),
    Column('tag_id', Integer, ForeignKey('tags.uid'))
)

class Rosbag(Base):
    __tablename__ = "rosbag"
    uid = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey('rosbag_store.uid'))
    store_data = Column(JSON)
    name = Column(String(255))
    is_extracted = Column(Boolean, server_default="false")
    in_trash = Column(Boolean, server_default="false")
    discovered = Column(DateTime, server_default="now() AT TIME ZONE 'utc'")
    meta_available = Column(Boolean)
    extraction_failure = Column(Boolean, server_default="false")
    size = Column(Integer)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Float)
    messages = Column(Integer)
    comment = Column(String)  # This is more of a description

    # Relationship
    store = relationship("RosbagStore", back_populates="bags")
    products = relationship("RosbagProduct", cascade="all, delete-orphan")
    topics = relationship("RosbagTopic", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=tag_association_table)
    comments = relationship("RosbagComment", cascade="all, delete-orphan")

    def to_swagger_model_summary(self, model=None, user=None):
        if model is None:
            model = BagSummary()

        model.detail_type="BagSummary"
        model.name=self.name
        model.store_data=hide(self.store_data, user, Permissions.StoreSecretAccess, {"_hidden": True})
        model.discovered=self.discovered
        model.is_extracted=self.is_extracted
        model.in_trash=self.in_trash
        model.extraction_failure = self.extraction_failure
        model.meta_available=self.meta_available
        model.size=self.size
        model.start_time=self.start_time
        model.end_time=self.end_time
        model.duration=self.duration
        model.messages=self.messages
        model.tags = [x.to_swagger_model() for x in self.tags]
        return model

    def to_swagger_model_detailed(self, user=None):
        model = self.to_swagger_model_summary(BagDetailed(), user=user) #type: BagDetailed
        model.detail_type = "BagDetailed"
        model.comment = self.comment

        model.topics = []
        for t in self.topics:
            model.topics.append(t.to_swagger_model_detailed())

        model.products = []
        for p in self.products:
            model.products.append(p.to_swagger_model_detailed())

        return model

    def from_swagger_model(self, api_model, user=None):
        model = api_model  # type: BagDetailed
        self.name = model.name
        if has_permission(user, Permissions.StoreSecretAccess):
            self.store_data = model.store_data
        self.discovered = model.discovered.replace(tzinfo=None) if model.discovered else None
        self.is_extracted = model.is_extracted
        self.in_trash = model.in_trash
        self.extraction_failure = model.extraction_failure
        self.meta_available = model.meta_available
        self.size = model.size
        self.start_time = model.start_time.replace(tzinfo=None) if model.start_time else None
        self.end_time = model.end_time.replace(tzinfo=None) if model.end_time else None
        self.duration = model.duration
        self.messages = model.messages
        self.comment = model.comment

        return self
