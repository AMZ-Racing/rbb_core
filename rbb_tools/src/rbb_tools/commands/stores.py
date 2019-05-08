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
import logging
import os
import re
import shutil

import rbb_storage
import rbb_tools.commands.config
import rbb_tools.commands.download
import rbb_tools.commands.upload
from rbb_client.models.bag_store_detailed import BagStoreDetailed
from rbb_tools.extraction.extractor import Extractor
from rbb_tools.common.storage import Storage


def list(api):
    try:
        stores = api.list_stores()

        for store in stores:
            print("- %s (%s)" % (store.name, store.store_type))
    except Exception as e:
        print("Reason: " + str(e))


def create(api, store_name, description, store_type, default_file_store, options):
    regex = r"^([a-z0-9\-]+)$"
    if not re.search(regex, store_name):
        print ("Store name can only contain lower case characters and dashes")
        return

    if not Storage.plugin_exists(store_type):
        print ("Store type '%s' is not installed on your system" % store_type)
        return

    store = Storage.factory(store_name, store_type, {})
    auth_required = store.new(options)

    store_model = BagStoreDetailed()
    store_model.detail_type='BagStoreDetailed'
    store_model.name=store_name
    store_model.description=description
    store_model.store_type=store_type
    store_model.store_data=store.get_data()
    store_model.created=datetime.datetime.utcnow()
    store_model.default_file_store = default_file_store

    try:
        api.put_store(store_name, store_model)
    except Exception as e:
        print("Failure during save of store on server. (%s)" % str(e))
        return

    if auth_required:
        url = "%s/stores/%s/authorize/0" % (api.api_client.host, store_name)
        print("Store saved on server, please complete the setup by going to %s" % url)
    else:
        print("Store saved on server!")


def process_store(api, store_name, configurations, tmp_dir="", output_dir="", rules="", no_clean=False):
    if tmp_dir == "":
        tmp_dir = "temp"

    if output_dir == "":
        output_dir = "output"

    if len(configurations) == 0:
        print("Using auto configuration, retrieving configurations from server...")
        try:
            configs = api.get_store_extraction_configs(store_name)

            for config in configs:
                config_path = os.path.realpath(tmp_dir + "/config/" + config.name)
                print("Downloading config '%s' from server -> %s" % (config.name, config_path))
                if os.path.exists(config_path):
                    shutil.rmtree(config_path)

                os.makedirs(config_path)

                if rbb_tools.commands.config.download(api, config.name, config_path, tmp_dir=tmp_dir + "/config_tmp"):
                    configurations.append(config_path + "/config.yaml")

        except Exception as e:
            logging.exception("Cannot get configuration from server", exc_info=e)
            return

    if len(configurations) == 0:
        print("No configurations found!")
        return

    bags = []
    try:
        bags = api.list_bags(store_name)
    except Exception as e:
        logging.exception("Cannot list bags from server", e)
        return

    for bag in bags:
        if bag.meta_available:
            print("Skipping '%s'" % bag.name)
            continue

        print("Processing '%s'" % bag.name)
        bag_output_dir = os.path.realpath(output_dir + "/" + bag.name)

        try:
            fresh_data = api.get_bag_meta(store_name, bag.name)

            if not fresh_data.meta_available:
                process_single_bag(api, store_name, bag.name, configurations, tmp_dir + "/bag", bag_output_dir, rules, no_clean)
        except Exception as e:
            logging.exception("Exception during processing of %s" % bag.name, e)


def process_single_bag(api, store_name, bag_name, configurations, tmp_dir="", output_dir="", rules="", no_clean=False):
    if tmp_dir == "":
        tmp_dir = "temp"

    if output_dir == "":
        output_dir = "output"

    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    exception = False

    try:
        temporary_bag_name = os.path.realpath(tmp_dir + "/" + bag_name)

        # Download
        rbb_tools.commands.download.command(store_name, bag_name, api, save_name=temporary_bag_name)

        for configuration in configurations:
            # Process
            ex = Extractor(
                configuration,
                temporary_bag_name,
                tmp_dir,
                output_dir,
                False,
                True,
                rules)
            ex.run()

            manifest_path = os.path.realpath(output_dir + "/manifest.yaml")
            ex.write_manifest(manifest_path, {
                    'server_url': api.api_client.host,
                    'store_name': store_name,
                    'bag_name': bag_name,
                })

            # Upload
            rbb_tools.commands.upload.command(manifest_path, "", api)

            # Empty temporary dir
            shutil.rmtree(tmp_dir)
            os.makedirs(tmp_dir)

    except Exception as e:
        logging.exception("Exception during process", exc_info=e)
        exception = True
    finally:
        if not no_clean:
            print("Cleaning up...")
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)

    return not exception

