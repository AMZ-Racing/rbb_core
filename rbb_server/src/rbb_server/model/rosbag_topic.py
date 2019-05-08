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

from rbb_swagger_server.models import Topic
from .base import Base


class RosbagTopic(Base):
    __tablename__ = "rosbag_topic"
    uid = Column(Integer, primary_key=True)
    bag_id = Column(Integer, ForeignKey('rosbag.uid'))
    name = Column(String(255))
    msg_type = Column(String(255))
    msg_type_hash = Column(String(50))
    msg_definition = Column(String)
    msg_count = Column(Integer)
    avg_frequency = Column(Float)

    # Relationships
    bag = relationship("Rosbag", back_populates="topics")

    def to_swagger_model_detailed(self, user=None):
        return Topic(
            name=self.name,
            msg_type=self.msg_type,
            msg_type_hash=self.msg_type_hash,
            msg_definition=self.msg_definition,
            msg_count=self.msg_count,
            avg_frequency=self.avg_frequency
        )

    def from_swagger_model(self, api_model):
        model = api_model  # type: Topic
        self.name = model.name
        self.msg_type = model.msg_type
        self.msg_type_hash = model.msg_type_hash
        self.msg_definition = model.msg_definition
        self.msg_count = model.msg_count
        self.avg_frequency = model.avg_frequency

        return self

