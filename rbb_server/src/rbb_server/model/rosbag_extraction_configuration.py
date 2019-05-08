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

from rbb_swagger_server.models import BagExtractionConfiguration as SwaggerBagExtractionConfiguration
from .base import Base


class RosbagExtractionConfiguration(Base):
    __tablename__ = "rosbag_extraction_configuration"
    uid = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(String(255))
    config_type = Column(String(255))
    config = Column(JSON)

    def to_swagger_model(self, user=None):
        return SwaggerBagExtractionConfiguration(
            name=self.name,
            description=self.description,
            type=self.config_type,
            config=self.config)

    def from_swagger_model(self, api_model, user=None):
        self.name = api_model.name
        self.description = api_model.description
        self.config_type = api_model.type
        self.config = api_model.config
