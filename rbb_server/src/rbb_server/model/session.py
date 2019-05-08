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

import base64

from sqlalchemy import *
from sqlalchemy.orm import relationship

from rbb_swagger_server.models import Session as SwaggerSession
from .base import Base


class Session(Base):
    __tablename__ = "token"
    uid = Column(Integer, primary_key=True)
    user_uid = Column(Integer, ForeignKey('rbb_user.uid'))
    token = Column(String(255))
    created = Column(DateTime, server_default="now() AT TIME ZONE 'utc'")
    valid_for = Column(Integer, server_default="86400")

    # Relationship
    user = relationship("User", back_populates="tokens")

    def to_swagger_model(self, show_token=False):
        model = SwaggerSession()
        model.created = self.created
        model.id = self.uid
        if show_token:
            model.token = base64.b64encode(("%d-%s" % (self.uid, self.token)).encode('latin1')).decode('latin1')
        return model

    def from_swagger_model(self, api_model):
        raise NotImplementedError()
