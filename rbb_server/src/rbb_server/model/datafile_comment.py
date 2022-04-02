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

from sqlalchemy import *
from sqlalchemy.orm import relationship

from rbb_swagger_server.models import Comment
from .base import Base


class DataFileComment(Base):
    __tablename__ = "datafile_comment"
    uid = Column(Integer, primary_key=True)
    datafile_id = Column(Integer, ForeignKey('datafile.uid'))
    user_id = Column(Integer, ForeignKey('rbb_user.uid'))
    comment_text = Column(String(1000))
    created = Column(DateTime, server_default="now() AT TIME ZONE 'utc'")

    # Relationship
    datafile = relationship("DataFile", back_populates="comments")
    user = relationship("User")

    def to_swagger_model(self, model=None, user=None):
        if not model:
            model = Comment()

        model.identifier = self.uid
        model.created = self.created
        model.comment_text = self.comment_text

        if self.user_id:
            model.posted_by = self.user.to_swagger_model()
        else:
            model.posted_by = None

        return model

    def from_swagger_model(self, api_model):
        self.comment_text = api_model.comment_text
        self.created = api_model.created.replace(tzinfo=None)
        pass


