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

import logging
import os

import dropbox
import dropbox.files
import dropbox.oauth

import rbb_storage


class DropboxStoragePlugin(rbb_storage.StoragePluginBase):

    def __init__(self, name, data, config_provider):
        super(DropboxStoragePlugin, self).__init__(name, data, config_provider)

        if not 'dropbox' in data:
            data['dropbox'] = {}

        self._plugin_data = data['dropbox']
        self._dbx = None

    def list_files(self):
        dbx = self._get_dbx()
        folder = self._plugin_data['path']
        folder_lower_case = folder.lower()
        dir = dbx.files_list_folder(folder, recursive=True)

        files=[]
        while True:
            for file in dir.entries:
                if isinstance(file, dropbox.files.FileMetadata):
                    if folder_lower_case == file.path_lower[0:len(folder_lower_case)]:
                        relative_name = file.path_lower[len(folder_lower_case):]

                        safe_name = relative_name
                        if safe_name[0] == '/' or safe_name[0] == '\\':
                            safe_name = safe_name[1:]

                        safe_name = safe_name.replace('/', '_')
                        safe_name = safe_name.replace('\\', '_')

                        files.append(rbb_storage.StoredFile(
                            safe_name,
                            file.name,
                            relative_name,
                            {
                                'id': file.id,
                                'path': file.path_lower
                            }
                        ))

            if dir.has_more:
                dir = dbx.files_list_folder_continue(dir.cursor)
            else:
                break

        return files

    def list_file(self, file_data):
        # TODO: Extract this into a function together with the code in list_files
        folder = self._plugin_data['path']
        file_path = file_data['path']
        folder_lower_case = folder.lower()
        relative_name = file_path[len(folder_lower_case):]

        safe_name = relative_name
        if safe_name[0] == '/' or safe_name[0] == '\\':
            safe_name = safe_name[1:]

        safe_name = safe_name.replace('/', '_')
        safe_name = safe_name.replace('\\', '_')

        return rbb_storage.StoredFile(
                            safe_name,
                            os.path.basename(relative_name),
                            relative_name,
                            file_data
                        )

    def download_link(self, file_data):
        dbx = self._get_dbx()

        if 'path' not in file_data:
            raise RuntimeError("Path not defined in file data")

        result = dbx.files_get_temporary_link(file_data['path'])
        return result.link

    def delete_file(self, file_data):
        raise NotImplementedError()

    def store_file(self, local_path, mime_type, name_hint="", directory_hint="", progress_indicator=True):
        raise NotImplementedError()

    def _is_linked_to_account(self):
        return 'token' in self._plugin_data and self._plugin_data['token'] != "";

    def _set_account_token(self, token):
        self._plugin_data['token'] =  token

    def _get_dbx(self):
        if self._dbx is None:
            self._dbx = dropbox.Dropbox(self._plugin_data['token'])
        return self._dbx

    def new(self, command_line_args):
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', '--path', default="", help="Root path of the store")
        parser.add_argument('-t', '--token', default="", help="Authorization token")
        args = parser.parse_args(command_line_args)

        self._plugin_data['path'] = args.path

        if args.token:
            self._plugin_data['token'] = args.token
            return False
        else:
            self._plugin_data['token'] = ""
            return True

    def authorize_get_step(self, step, flask_request, url):
        if self._is_linked_to_account():
            return "Already authorized"

        import flask

        if step == "0":
            return self.authorize_step_0(flask_request, url)
        else:
            return flask.redirect(url + "0", code=302)

    def authorize_post_step(self, step, flask_request, url):
        if self._is_linked_to_account():
            return "Already authorized"

        import flask

        if step == "1":
            return self.authorize_step_1(flask_request, url)
        else:
            return flask.redirect(url + "0", code=302)

    def _get_auth_flow(self):
        config = self._config_provider.get_configuration_key("secret.dropbox")
        if not 'secret' in config or not 'dropbox' in config['secret']:
            raise RuntimeError("Config keys in secret.dropbox missing!")

        consumer_key = config['secret']['dropbox']['app_key']
        consumer_secret = config['secret']['dropbox']['app_secret']
        flow = dropbox.oauth.DropboxOAuth2FlowNoRedirect(consumer_key, consumer_secret)
        return flow

    def authorize_step_0(self, flask_request, url):

        flow = self._get_auth_flow()
        dropbox_auth_url = flow.start()
        next_step_url = url + "1"

        page_html = """
        <html>
            <head><title>Dropbox Authorization</title></head>
            <body>
                <p>Please get a dropbox authorization code at the following link, <a target="_blank" href="%s">%s</a></p>
                <p>Paste the code here:
                    <form action="%s" method="POST">
                        <input type="text" name="dropbox_code"></input><input type="submit"></input>
                    </form>
                </p>
            </body>
        </html>
        """ % (dropbox_auth_url, dropbox_auth_url, next_step_url)

        import flask
        return flask.Response(page_html)

    def authorize_step_1(self, flask_request, url):
        code = flask_request.form.get('dropbox_code')

        if code:
            try:
                flow = self._get_auth_flow()
                result = flow.finish(code)

                if result.access_token:
                    self._set_account_token(result.access_token)
                    self.save()
                    return "Authorization succeeded!"
                else:
                    return "Authorization failed!"
            except Exception as e:
                logging.exception("Dropbox authorization failed", e)
                return "Error occured (" + str(e) + ")"
        else:
            return "Invalid code!"


plugin = DropboxStoragePlugin