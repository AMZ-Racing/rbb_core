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

from flask import url_for
from rbb_server.helper.permissions import hide, Permissions, has_permission
from sqlalchemy import *
from sqlalchemy.orm import relationship

from rbb_swagger_server.models import FileSummary, FileDetailed
from .base import Base


class File(Base):
    __tablename__ = "file"
    uid = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey('file_store.uid'))
    name = Column(String(255))
    store_data = Column(JSON)

    # Relationship
    store = relationship("FileStore", back_populates="files")

    def to_swagger_model_summary(self, model=None):
        if model is None:
            model = FileSummary()
        model.detail_type = "FileSummary"
        model.uid = self.uid
        model.store_name = self.store.name
        model.name = self.name
        model.link = url_for(
            "/api/v0.rbb_server_controllers_file_controller_get_file",
            file_name = self.name,
            store_name = self.store.name,
            uid = self.uid,
            _external=True
        )
        return model

    def to_swagger_model_detailed(self, model=None, user=None):
        if model is None:
            model = FileDetailed()
        model.detail_type = "FileDetailed"
        model.uid = self.uid
        model.store_name = self.store.name
        model.name = self.name
        model.store_data = hide(self.store_data, user, Permissions.StoreSecretAccess)

        model.link = url_for(
            "/api/v0.rbb_server_controllers_file_controller_get_file",
            file_name = self.name,
            store_name = self.store.name,
            uid = self.uid,
            _external=True
        )
        return model

    def from_swagger_model(self, api_model, user=None):
        model = api_model  # type: FileDetailed
        self.uid = model.uid
        self.name = model.name

        if has_permission(user, Permissions.StoreSecretAccess):
            self.store_data = model.store_data

        return self