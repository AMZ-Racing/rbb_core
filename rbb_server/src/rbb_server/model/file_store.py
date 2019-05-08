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

from rbb_server.helper.permissions import has_permission, Permissions
from sqlalchemy import *
from sqlalchemy.orm import relationship

from rbb_swagger_server.models import FileStore as SwaggerFileStore
from .base import Base


class FileStore(Base):
    __tablename__ = "file_store"
    uid = Column(Integer, primary_key=True)
    name = Column(String(100))
    store_type = Column(String(50))
    store_data = Column(JSON)
    created = Column(DateTime(), server_default="now() AT TIME ZONE 'utc'")

    # Relationship
    files = relationship("File", cascade="all, delete-orphan")

    def to_swagger_model(self, user=None):

        data = {'_hidden': True}
        if has_permission(user, Permissions.StoreSecretAccess):
            data = self.store_data
            data['_hidden'] = False

        return SwaggerFileStore(
            name=self.name,
            store_type=self.store_type,
            store_data=data,
            created=self.created
        )

    def from_swagger_model(self, api_model, user=None):
        self.name = api_model.name
        self.created = api_model.created

        if has_permission(user, Permissions.StoreSecretAccess):
            self.store_type = api_model.store_type
            self.store_data = api_model.store_data
