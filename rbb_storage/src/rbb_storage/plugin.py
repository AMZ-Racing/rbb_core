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
import hashlib
import random
import time
import uuid


class StoredFile(object):

    def __init__(self, save_name, normal_name, full_path, data):
        """
        Information about a file stored in a file store

        :param save_name: Unique name for the file in the store.
                          This is presented to the user (directory structure needs to be flattened, NEEDS to be url safe).
        :param normal_name: Name of the file itself (without path)
        :param full_path: Full path to the file (Relative to the root of the store)
        :param data: Data specific to the file store
        """
        self._save_name = save_name
        self._normal_name = normal_name
        self._full_path = full_path
        self._data = data

    def get_save_name(self):
        return self._save_name

    def get_name(self):
        return self._normal_name

    def get_path(self):
        return self._full_path

    def get_data(self):
        return self._data

    def __repr__(self):
        return "save_name=%s, path=%s, data=%s" % (self._save_name, self._full_path, self._data)


class StoragePluginBase(object):

    def __init__(self, name, data, config_provider):
        self._name = name
        self._data = data
        self._needs_saving = False
        self._config_provider = config_provider

    def get_data(self):
        return self._data

    def _unique_hash_name_url(self, string=""):
        anti_collision = "%f%f%d" % (random.random(), time.time(), uuid.getnode())
        output = base64.b64encode(hashlib.sha512(anti_collision + string).digest())
        output = output.replace("/","-")
        output = output.replace("+","_")
        return output.replace("=","")

    def is_indexable(self):
        """
        Can this store be indexed

        :return: True if the store can be indexed
        """
        if 'indexable' not in self._data:
            return True

        return self._data['indexable']

    def list_files(self):
        """
        List all files in the store

        :return: An array of StoredFile's
        """

        raise NotImplementedError()

    def list_file(self, file_data):
        """
        List information about a single file in the store

        :return: The StoredFiled information
        """

        raise NotImplementedError()

    def download_link(self, file_data):
        """
        http(s) link to the file.
        :param file_data:
        :return:
        """
        raise NotImplementedError()

    def delete_file(self, file_data):
        """
        Delete file from the store

        :param file_data:
        :return:
        """
        raise NotImplementedError()

    def store_file(self, local_path, mime_type, name_hint="", directory_hint="", progress_indicator=True):
        """
        Store a file on the local filesystem in the file store

        :param local_path: Path to the file on the local filesystem
        :param mime_type: Mimetype of the file
        :param name_hint: Hint for the underlying storage system to name the file
        :param directory_hint:  Hint for the underlying storage system to name the path
        :param progress_indicator:
        :return:
        """
        raise NotImplementedError()

    def save(self):
        """
        Should be called by the plugin implementation in authorize_get_step & authorize_post_step
        to signal that the store_data needs to be saved.

        :return:  Nothing
        """
        self._needs_saving = True

    def needs_saving(self):
        """
        Function to check if the plugin changed its store_data.

        :return: True if the store_data needs to be saved to the database
        """
        return self._needs_saving

    def new(self, command_line):
        """
        Initialize this store as new. Function returns true if online authentication is required.

        :param command_line: Command line parameters for initialization
        :type command_line: str

        :rtype: bool
        """
        raise NotImplementedError()

    def authorize_get_step(self, step, flask_request, url):
        return self.authorize_post_step(step, flask_request, url)

    def authorize_post_step(self, step, flask_request, url):
        page_html = """
        <html>
            <head><title>Store Authorization</title></head>
            <body>
                <p>This store does not require authorization.</p>
            </body>
        </html>
        """

        import flask
        return flask.Response(page_html)
