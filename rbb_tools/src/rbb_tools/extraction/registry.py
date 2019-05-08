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

import datetime
import os


class Product(object):

    def __init__(self, config_tag, from_rule, plugin, base_directory):
        self._config_tag = config_tag
        self._from_rule = from_rule
        self._plugin = plugin
        self._created = datetime.datetime.utcnow()
        self._base_directory = base_directory

        self._title = ""
        self._type = ""
        self._files = {}
        self._data = {}
        self._topics = {}

    def get_type(self):
        return self._type

    def get_title(self):
        return self._title

    def set_type(self, type):
        self._type = type

    def set_title(self, title):
        self._title = title

    def add_file(self, key, path, mime="application/octet-stream", overwrite_if_exists=False):
        if key in self._files and not overwrite_if_exists:
            raise RuntimeError("File with key %s already exists" % key)

        full_path = self._base_directory + "/" + path
        if not os.path.exists(full_path):
            raise RuntimeError("Cannot find file %s with key %s" % (full_path, key))

        self._files[key] = {
            'path': full_path,
            'mime': mime
        }

    def set_data(self, data):
        self._data = data

    def set_topics(self, topics):
        self._topics = topics

    def to_dict(self):
        return {
            'config_tag': self._config_tag,
            'rule': self._from_rule,
            'plugin': self._plugin,
            'title': self._title,
            'product_type': self._type,
            'product_data': self._data,
            'created': self._created,
            'topics': self._topics,
            'files': self._files,
        }


class ProductFactory(object):

    def __init__(self, config_tag, from_rule, plugin, base_directory):
        self._config_tag = config_tag
        self._from_rule = from_rule
        self._plugin = plugin
        self._base_directory = base_directory

    def new(self):
        return Product(self._config_tag, self._from_rule, self._plugin, self._base_directory)