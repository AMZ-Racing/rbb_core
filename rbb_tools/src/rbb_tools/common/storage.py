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

import rbb_storage.storage
from rbb_storage.storage import StoragePluginNotFound


class ClientStorageConfigurationProvider(rbb_storage.storage.AbstractStorageConfigurationProvider):

    _api = None

    @classmethod
    def set_api(cls, api):
        cls._api = api

    @classmethod
    def get_configuration_key(cls, config_key):
        if cls._api is None:
            raise RuntimeError("ClientStorageConfigurationProvider api not set, use the set_api method to set the api.")

        config = dict(cls._api.get_configuration_key(config_key))
        return config


class Storage(rbb_storage.storage.Storage):

    @classmethod
    def initialize(cls, api):
        ClientStorageConfigurationProvider.set_api(api)

    @classmethod
    def factory(cls, store_name, store_type, store_data):
        return cls.factory_with_config_provider(store_name, store_type, store_data, ClientStorageConfigurationProvider)

