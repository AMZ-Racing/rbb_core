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

import importlib
import logging

import rbb_storage.plugin


class StoragePluginNotFound(Exception):
    pass


class AbstractStorageConfigurationProvider:
    @classmethod
    def get_configuration_key(cls, config_key):
        raise NotImplementedError("AbstractStorageConfigurationProvider needs to be "
                                  "specialized for client or server side")


class Storage(object):

    @classmethod
    def plugin_exists(cls, store_type):
        try:
            plugin = importlib.import_module(store_type + ".plugin")

            if issubclass(plugin.plugin, rbb_storage.StoragePluginBase):
                return True

        except ImportError as e:
            pass

        return False


    @classmethod
    def factory(cls, store_name, store_type, store_data):
        # Overwritten for client or server side specialization
        # Server side configuration is retrieved directly from the Database
        # Client side is requested through the RBB API
        raise NotImplementedError()


    @classmethod
    def factory_with_config_provider(cls, store_name, store_type, store_data, config_provider):
        try:
            plugin = importlib.import_module(store_type + ".plugin")
        except ImportError as e:
            logging.error(str(e))
            raise StoragePluginNotFound()

        if not issubclass(plugin.plugin, rbb_storage.StoragePluginBase):
            raise StoragePluginNotFound()

        return plugin.plugin(store_name, store_data, config_provider)