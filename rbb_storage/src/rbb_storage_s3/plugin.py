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

import os
import sys

import boto3
from botocore import UNSIGNED
from botocore.client import Config as ClientConfig

import rbb_storage

try:
    from urllib import quote  # Python 2
except ImportError:
    from urllib.parse import quote  # Python 3


class ProgressPrinter(object):
    def __init__(self, size, show=True):
        self._size = size
        self._uploaded = 0
        self._show = show

    def __call__(self, uploaded):
        if not self._show:
            return

        self._uploaded += uploaded
        mb_total= self._size / (1024.0 * 1024.0)
        mb_uploaded = self._uploaded / (1024.0 * 1024.0)
        percentage = mb_uploaded / mb_total * 100.0
        sys.stdout.write("%.2f%% (%.2f/%.2f mb)   \r" % (percentage, mb_total, mb_uploaded))
        sys.stdout.flush()

    def clear(self):
        if not self._show:
            return

        sys.stdout.write("                                                            \r")
        sys.stdout.flush()


class AmazonS3StoragePlugin(rbb_storage.StoragePluginBase):

    def __init__(self, name, data, config_provider):
        super(AmazonS3StoragePlugin, self).__init__(name, data, config_provider)
        self._plugin_data = data['s3']
        self._client = None

    def _get_s3_objects(self):
        s3 = self._get_client()
        kwargs = {
            'Bucket': self._get_bucket(),
            'Prefix': self._get_prefix()
        }

        while True:
            resp = s3.list_objects_v2(**kwargs)

            try:
                contents = resp['Contents']
            except KeyError:
                return

            for obj in contents:
                yield obj

            try:
                kwargs['ContinuationToken'] = resp['NextContinuationToken']
            except KeyError:
                break

    def list_files(self):
        # Kept for compatability, all stores now have the indexable property
        if not self._is_indexable():
            raise RuntimeError("This store is not marked as indexable!")

        files=[]
        for s3_object in self._get_s3_objects():
            key = s3_object['Key']

            relative_name = key.lower()[len(self._get_prefix()):]
            file_name = relative_name.split('/')[-1]

            if not file_name.strip():
                continue

            safe_name = relative_name
            if safe_name[0] == '/' or safe_name[0] == '\\':
                safe_name = safe_name[1:]

            safe_name = safe_name.replace('/', '_')
            safe_name = safe_name.replace('\\', '_')

            files.append(rbb_storage.StoredFile(
                safe_name,
                file_name,
                relative_name,
                {
                    's3': {
                        'path': key[len(self._get_prefix()):]
                    }
                }
            ))

        return files

    def list_file(self, file_data):
        # TODO: Extract this into a function together with the code in list_files
        relative_name = file_data['s3']['path']
        file_name = relative_name.split('/')[-1]
        safe_name = relative_name
        if safe_name[0] == '/' or safe_name[0] == '\\':
            safe_name = safe_name[1:]

        safe_name = safe_name.replace('/', '_')
        safe_name = safe_name.replace('\\', '_')

        return rbb_storage.StoredFile(
                            safe_name,
                            file_name,
                            relative_name,
                            file_data
                        )

    def download_link(self, file_data):
        if self._use_signed_links():
            client = self._get_client()
            return client.generate_presigned_url('get_object',
                                                 ExpiresIn=3600,
                                                 Params={
                                                     'Bucket': self._get_bucket(),
                                                     'Key': self._get_file_key(file_data)})
        else:
            return "https://%s.s3.amazonaws.com/%s" % (quote(self._get_bucket()), quote(self._get_file_key(file_data)))

    def delete_file(self, file_data):
        raise NotImplementedError()

    def store_file(self, local_path, mime_type, name_hint="", directory_hint="", progress_indicator=True):
        print("S3: Storing %s (%s) (%s|%s)" % (local_path, mime_type, directory_hint, name_hint))

        path = directory_hint + "/" + self._unique_hash_name_url()
        key = self._plugin_data["key_prefix"] + path

        progress = ProgressPrinter(os.path.getsize(local_path), progress_indicator)

        client = self._get_client()
        client.upload_file(local_path, self._get_bucket(), key, Callback=progress, ExtraArgs={
            "ContentType": mime_type,
            "ACL": "public-read"
            })

        progress.clear()

        return {
            's3': {
                'path': path
            }
        }

    def _get_object(self, file_data):
        client = self._get_client()
        return client.Object(self._get_bucket(), self._get_file_key(file_data))

    def _get_file_key(self, file_data):
        return self._get_prefix() + file_data['s3']['path']

    def _get_prefix(self):
        if "key_prefix" in self._plugin_data:
            return self._plugin_data["key_prefix"]
        else:
            return ""

    def _is_indexable(self):
        return "indexable" in self._plugin_data and self._plugin_data["indexable"]

    def _use_signed_links(self):
        return "signed_links" in self._plugin_data and self._plugin_data["signed_links"]

    def _get_bucket(self):
        return self._plugin_data['bucket']

    def _get_client(self, unsigned=False):
        endpoint_url = self._plugin_data['endpoint-url'] if 'endpoint-url' in self._plugin_data else False

        if unsigned:
            config = ClientConfig()
            config.signature_version = UNSIGNED
            if endpoint_url:
                return boto3.client('s3',
                                    endpoint_url=endpoint_url,
                                    config=config,
                                    aws_access_key_id="{YOUR_ACCESS_KEY_ID}",
                                    aws_secret_access_key="{YOUR_SECRET_ACCESS_KEY}")
            else:
                return boto3.client('s3',
                                    config=config,
                                    aws_access_key_id="{YOUR_ACCESS_KEY_ID}",
                                    aws_secret_access_key="{YOUR_SECRET_ACCESS_KEY}")

        if self._client is None:
            if endpoint_url:
                self._client = boto3.client(
                    's3',
                    endpoint_url=endpoint_url,
                    aws_access_key_id=self._plugin_data['aws-access-key-id'],
                    aws_secret_access_key=self._plugin_data['aws-secret-access-key']
                )
            else:
                self._client = boto3.client(
                    's3',
                    aws_access_key_id=self._plugin_data['aws-access-key-id'],
                    aws_secret_access_key=self._plugin_data['aws-secret-access-key']
                )
        return self._client


plugin = AmazonS3StoragePlugin