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

import yaml

import rbb_storage
from rbb_tools.common.storage import Storage
from rbb_client.models.bag_detailed import BagDetailed
from rbb_client.models.bag_store_detailed import BagStoreDetailed
from rbb_client.models.file_detailed import FileDetailed
from rbb_client.models.file_store import FileStore
from rbb_client.models.product import Product
from rbb_client.models.product_file import ProductFile
from rbb_client.models.topic import Topic
from rbb_client.models.topic_mapping import TopicMapping


def get_file_store(store_name, api):
    store = api.get_file_store(store_name)  # type: FileStore
    return Storage.factory(store.name, store.store_type, store.store_data)


def command(manifest_path, forced_file_store, api, progress_indicator=True):
    manifest = None

    if os.path.isdir(manifest_path):
        print("Cannot upload a directory, please specify the manifest file!")
        return

    with open(manifest_path, 'r') as stream:
        try:
            manifest = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise RuntimeError("Invalid YAML in configuration file: %s" % str(exc))

    if not manifest:
        print("Cannot load manifest file")
        return

    if not 'server_info' in manifest:
        print("Server info not in manifest, add it or override on the command line")
        return
    server_info = manifest['server_info']

    if not 'bag_name' in server_info or not 'server_url' in server_info or not 'store_name' in server_info:
        print("Server info not complete in manifest (bag_name, server_url and store_name are needed)")
        return

    bag_name = server_info['bag_name']
    server_url = server_info['server_url']
    store_name = server_info['store_name']

    api.api_client.host = server_url

    # Get bag store information
    try:
        bag_store = api.get_store(store_name)  # type: BagStoreDetailed
    except Exception as e:
        print("Cannot get bag store information from server using host '%s'" % server_url)
        print("Reason: " + str(e))
        return

    # Do we have a default file store?
    file_store_name = bag_store.default_file_store
    if forced_file_store:
        file_store_name = forced_file_store

    if not file_store_name:
        print("There is no default file store available for your bag, "
              "please specifiy one with the --file-store option.")
        return
    elif file_store_name != forced_file_store:
        print("Using default filestore '%s'" % file_store_name)

    # Prepare file store
    try:
        file_store = get_file_store(file_store_name, api)
    except Exception as e:
        print("Cannot get file store information from server using host '%s'" % server_url)
        print("Reason: " + str(e))
        return

    # Check if we can reach the bag before we start uploading
    try:
        bag_meta = api.get_bag_meta(store_name, bag_name)  # type: BagDetailed
    except Exception as e:
        print("Cannot list bags from server using host '%s'" % server_url)
        print("Reason: " + str(e))
        return

    print("Uploading products...")
    uploaded_files = {}
    products = []
    # Upload and fill products
    for product in manifest['products']:
        print("Uploading '%s'" % product['title'])

        files = []
        for product_file_key in product['files']:
            product_file = product['files'][product_file_key]

            file_model = None
            if product_file['path'] not in uploaded_files:
                file_name = os.path.basename(product_file['path'])

                print("Uploading file '%s' to storage '%s'..." % (file_name, file_store_name))

                file_data = file_store.store_file(
                    product_file['path'],
                    product_file['mime'],
                    directory_hint=store_name+"/"+bag_name,
                    name_hint=file_name,
                    progress_indicator=progress_indicator
                    )

                file_model = FileDetailed()
                file_model.detail_type="FileDetailed"
                file_model.store_name=file_store_name
                file_model.name=file_name
                file_model.store_data=file_data

                file_model = api.new_file(file_store_name, file_model)

                print("Created file %s with uid %s in store %s" % (file_model.name, str(file_model.uid), file_model.store_name))

                uploaded_files[product_file['path']] = file_model
            else:
                file_model = uploaded_files[product_file['path']]

            product_file_model = ProductFile()
            product_file_model.key = product_file_key
            product_file_model.file = file_model
            files.append(product_file_model)

        topics = []
        for topic in product['topics']:
            topic_mapping_model = TopicMapping()
            topic_mapping_model.original_topic = topic
            topic_mapping_model.plugin_topic = product['topics'][topic]
            topics.append(topic_mapping_model)

        product_model = Product()

        product_model.uid=""
        product_model.plugin=product['plugin']
        product_model.product_type=product['product_type']
        product_model.product_data=product['product_data']
        product_model.created=product['created']
        product_model.title=product['title']
        product_model.configuration_tag=product['config_tag']
        product_model.configuration_rule=product['rule']
        product_model.topics=topics
        product_model.files=files

        products.append(product_model)

    # Now we update the information
    try:
        bag_meta = api.get_bag_meta(store_name, bag_name)  # type: BagDetailed
    except Exception as e:
        print("Cannot list bags from server using host '%s'" % server_url)
        print("Reason: " + str(e))
        return

    if not bag_meta.meta_available:
        # Fill standard info
        bag_info = manifest['bag_info']
        bag_meta.size = bag_info['size']
        bag_meta.start_time = bag_info['start_time']
        bag_meta.end_time = bag_info['end_time']
        bag_meta.duration = bag_info['duration']
        bag_meta.messages = bag_info['messages']
        bag_meta.is_extracted = True
        bag_meta.meta_available = True

        # Fill topic info
        bag_meta.topics = []
        for topic in bag_info['topics']:
            topic_model = Topic()
            topic_model.name = topic['name']
            topic_model.msg_type = topic['msg_type']
            topic_model.msg_type_hash = topic['msg_type_hash']
            topic_model.msg_count = topic['msg_count']
            topic_model.msg_definition = topic['msg_definition']
            topic_model.avg_frequency = 0 if topic['avg_frequency'] is None else topic['avg_frequency']
            bag_meta.topics.append(topic_model)
    else:
        print("Meta information already uploaded to server, skipping meta upload.")

    # Remove old products (naive way, could be made faster in case of many producst)
    removed = 0
    for product in products:
        if not product.configuration_tag or not product.configuration_rule:
            continue

        len_before = len(bag_meta.products)
        # Filter out products with same config rule
        bag_meta.products = [x for x in bag_meta.products if not (
                x.configuration_tag == product.configuration_tag and
                x.configuration_rule == product.configuration_rule
        )]

        removed += len_before - len(bag_meta.products)

    print("Removed %d outdated product(s) from the bag information." % removed)

    # Add the new products
    for product in products:
        bag_meta.products.append(product)

    # Reset the failure flag
    bag_meta.extraction_failure = False

    # Save meta info
    api.put_bag_meta(store_name, bag_name, bag_meta)