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
from werkzeug.security import check_password_hash, generate_password_hash

from rbb_swagger_server.models import User as SwaggerUser
from .base import Base
from .permission import Permission

user_permission_association_table = Table('user_permissions', Base.metadata,
    Column('user_id', Integer, ForeignKey('rbb_user.uid')),
    Column('permission_id', String(50), ForeignKey('permission.uid'))
)

class User(Base):
    __tablename__ = "rbb_user"
    uid = Column(Integer, primary_key=True)
    alias = Column(String(50))
    full_name = Column(String(255))
    email = Column(String(300))
    password = Column(String(255))
    is_admin = Column(Boolean)

    has_credential_access = Column(Boolean)
    has_task_log_access = Column(Boolean)

    # Relationship
    tokens = relationship("Session", cascade="all, delete-orphan")
    permissions = relationship("Permission", secondary=user_permission_association_table)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def to_swagger_model(self, user=None):
        model = SwaggerUser()
        model.alias=self.alias
        model.full_name=self.full_name
        model.email=self.email
        model.password=None
        return model

    def from_swagger_model(self, api_model, user=None):
        self.alias = api_model.alias
        self.full_name = api_model.full_name
        self.email = api_model.email

        if api_model.password:
            self.set_password(api_model.password)

        return self