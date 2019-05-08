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

import rbb_storage


class StaticStoragePlugin(rbb_storage.StoragePluginBase):

    def __init__(self, name, data, config_provider):
        super(StaticStoragePlugin, self).__init__(name, data, config_provider)
        self._plugin_data = data['static']

    def list_files(self):
        files = []
        for file_name in self._plugin_data:
            files.append(rbb_storage.StoredFile(
                file_name,
                file_name,
                file_name,
                {
                    'link': self._plugin_data[file_name]['link'],
                    'name': file_name
                }
            ))

        return files

    def list_file(self, file_data):
        if 'name' not in file_data:
            return rbb_storage.StoredFile(
                "",
                "",
                "",
                {}
            )
        else:
            return rbb_storage.StoredFile(
                file_data['name'],
                file_data['name'],
                file_data['name'],
                file_data
            )

    def download_link(self, file_data):
        return file_data['link']

    def delete_file(self, file_data):
        raise NotImplementedError()

    def store_file(self, local_path, mime_type, name_hint="", directory_hint=""):
        raise NotImplementedError()


plugin = StaticStoragePlugin
