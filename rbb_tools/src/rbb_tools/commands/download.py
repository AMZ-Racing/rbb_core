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

import sys

import certifi
import urllib3

import rbb_client


def command(store_name, bag_name, api, save_name="", progress_indicator=True):
    try:
        url = api.api_client.host + ("/stores/%s/bags/%s" % (store_name, bag_name))
        print("Downloading %s..." % url)

        auth = rbb_client.configuration.auth_settings()
        headers = dict()
        headers[auth['basicAuth']['key']] = auth['basicAuth']['value']

        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where(), headers=headers)
        r = http.request('GET', url, preload_content=False, redirect=False)

        # Follow the redirect without the auth headers
        http.headers = dict()
        if r.get_redirect_location():
            r = http.request('GET', r.get_redirect_location(), preload_content=False)

        downloaded_length = 0
        content_length = 0
        if 'content-length' in r.headers:
            content_length = int(r.headers['content-length'])

        if save_name == "":
            save_name = bag_name

        with open(save_name, 'wb') as out:
            while True:
                if progress_indicator:
                    mb_download = downloaded_length / (1024.0 * 1024.0)
                    if content_length:
                        mb_total = content_length / (1024.0 * 1024.0)
                        sys.stdout.write("%.2f%% (%.2f/%.2f mb)   \r" % (mb_download / mb_total * 100, mb_total, mb_download))
                        sys.stdout.flush()
                    else:
                        sys.stdout.write("Unknown bag size, downloaded %.2f mb   \r" % (mb_download))
                        sys.stdout.flush()

                data = r.read(512*1024)
                downloaded_length += len(data)
                if not data:
                    break
                out.write(data)

        sys.stdout.write("                                                            \r")
        sys.stdout.flush()

        r.release_conn()
        print("Done!")

    except Exception as e:
        print("Reason: " + str(e))