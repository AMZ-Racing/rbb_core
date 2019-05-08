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

from rbb_swagger_server.models import BagStoreDetailed
from .base import Base

config_association_table = Table('rosbag_extraction_association', Base.metadata,
    Column('store_id', Integer, ForeignKey('rosbag_store.uid')),
    Column('config_id', Integer, ForeignKey('rosbag_extraction_configuration.uid'))
)

class RosbagStore(Base):
    __tablename__ = "rosbag_store"
    uid = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(String(255))
    created = Column(DateTime(), server_default="now() AT TIME ZONE 'utc'")
    store_type = Column(String(50))
    store_data = Column(JSON)
    default_file_store_id = Column(Integer, ForeignKey('file_store.uid'), nullable=True)

    # Relationship
    bags = relationship("Rosbag", cascade="all, delete-orphan")
    default_file_store = relationship("FileStore")
    auto_extraction_configs = relationship("RosbagExtractionConfiguration",
                    secondary=config_association_table)

    def to_swagger_model_detailed(self, user=None):
        return BagStoreDetailed(
            detail_type="BagStoreDetailed",
            name=self.name,
            description=self.description,
            store_type=self.store_type,
            store_data=hide(self.store_data, user, Permissions.StoreSecretAccess, {"_hidden": True}),
            created=self.created,
            default_file_store=self.default_file_store.name if self.default_file_store_id else ""
        )

    def from_swagger_model(self, api_model, user=None):
        model = api_model  # type: BagStoreDetailed
        self.name = model.name
        self.description = model.description
        self.created = model.created
        self.store_type = model.store_type
        if has_permission(user, Permissions.StoreSecretAccess):
            self.store_data = model.store_data

        return self

