# AMZ-Driverless
#  Copyright (c) 2022 Authors:
#   - Adrian Brandemuehl <abrandemuehl@gmail.com>
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

from flask import url_for
from rbb_server.helper.permissions import hide, Permissions, has_permission
from sqlalchemy import *
from sqlalchemy.orm import relationship

from rbb_server.model.user import User
from rbb_swagger_server.models import DataFileSummary, DataFileDetailed
from .base import Base

from typing import Union


class DataFile(Base):
    '''
    DataFile represents an arbitrary *data* file in storage. DataFile is
    different than File semantically because it is specifically for
    representing files that are readonly bits of data. They should not be
    '''
    __tablename__ = "datafile"
    uid = Column(Integer, primary_key=True)
    # Store that the data is stored on
    store_id = Column(Integer, ForeignKey('datafile_store.uid'))
    # Store specific data
    store_data = Column(JSON)
    # Name of the file
    name = Column(String(255))
    # File has been placed in trash for removal
    in_trash = Column(Boolean, server_default="false")
    # Time at which the data file was discover
    discovered = Column(DateTime, server_default="now() AT TIME ZONE 'utc'")
    # Indicates whether the metadata has been set
    meta_available = Column(Boolean)
    # Metadata fields
    # Size of the file in bytes
    size = Column(Integer)
    # Description of the file
    description = Column(String)
    # Type of the file.
    filetype = Column(String)

    # Relationship
    store = relationship("DatafileStore", back_populates="datafiles")
    tags = relationship("Tag", secondary=tag_association_table)

    def to_swagger_model_summary(self, model: Union[DataFileSummary,None]=None, user: Union[User,None]=None)-> DataFileSummary:
        if model is None:
            model = DataFileSummary()

        model.detail_type="DataFileSummary"
        model.name=self.name
        model.store_data=hide(self.store_data, user, Permissions.StoreSecretAccess, {"_hidden": True})
        model.discovered=self.discovered
        model.in_trash=self.in_trash
        model.meta_available=self.meta_available
        model.size=self.size
        model.tags = [x.to_swagger_model() for x in self.tags]
        return model

    def to_swagger_model_detailed(self, user: Union[User,None]=None) -> DataFileDetailed:
        model = self.to_swagger_model_summary(DataFileDetailed(), user=user)
        model.detail_type = "DataFileDetailed"
        model.description = self.description
        return model

    def from_swagger_model(self, api_model: DataFileDetailed, user: Union[User,None]=None) -> DataFile:
        model = api_model
        self.name = model.name
        if has_permission(user, Permissions.StoreSecretAccess):
            self.store_data = model.store_data
        self.discovered = model.discovered.replace(tzinfo=None) if model.discovered else None
        self.in_trash = model.in_trash
        self.meta_available = model.meta_available
        self.size = model.size
        self.description = model.description

        return self