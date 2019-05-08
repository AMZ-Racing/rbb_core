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

from rbb_swagger_server.models import Permission as SwaggerPermission
from .base import Base


class ConfigKeyValue(Base):
    __tablename__ = "configuration"
    config_key = Column(String(255), primary_key=True)
    value = Column(String())
    description = Column(String(255), server_default="''")

    @classmethod
    def get_config_dict(cls, config_key, session):
        # Check the store
        q = session.query(ConfigKeyValue)

        # Build dictionary
        dictionary = {}
        for kv in q:  # type: ConfigKeyValue
            key_parts = kv.config_key.split(".")

            leaf = dictionary
            for key_part in key_parts[:-1]:
                if not key_part in leaf:
                    leaf[key_part] = {}

                leaf = leaf[key_part]

            leaf[key_parts[-1]] = kv.value

        # TODO: Filter only requested key

        return dictionary

    def to_swagger_model(self):
        raise NotImplementedError()

    def from_swagger_model(self, api_model):
        raise NotImplementedError()
