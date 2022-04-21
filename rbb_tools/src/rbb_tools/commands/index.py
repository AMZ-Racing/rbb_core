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

from rbb_client.models.bag_detailed import BagDetailed
import datetime
from rbb_tools.common.storage import Storage, StoragePluginNotFound


def register_bag_file(api, store_name, file):
    bag = BagDetailed()
    bag.detail_type="BagDetailed"
    bag.name=file.get_save_name()
    bag.store_data=file.get_data()
    bag.size=0
    bag.meta_available=False
    bag.discovered=datetime.datetime.utcnow()
    bag.is_extracted=False
    bag.comment=""
    bag.topics=[]
    bag.products=[]
    bag.extraction_failure = False

    api.put_bag_meta(store_name, bag.name, bag)


def command(store_name, api):
    store_info = None
    store = None
    bags = []

    try:
        store_info = api.get_store(store_name)
    except Exception as e:
        print("Reason: " + str(e))
        return

    try:
        store = Storage.factory(store_info.name, store_info.store_type, store_info.store_data)
    except StoragePluginNotFound:
        print ("Cannot find plugin for storage type '%s'" % store_info.store_type)
        return

    if not store.is_indexable():
        print("This store has been marked as not indexable!")
        return

    try:
        bags = api.list_bags(store_name, in_trash=False)
        trashed_bags = api.list_bags(store_name, in_trash=True)
    except Exception as e:
        print("Reason: " + str(e))
        return

    bags_by_name = {}
    for bag in bags:
        info = store.list_file(bag.store_data)
        bags_by_name[info.get_path()] = bag

    trashed_bags_by_name = {}
    for bag in trashed_bags:
        info = store.list_file(bag.store_data)
        trashed_bags_by_name[info.get_path()] = bag

    store_files = store.list_files()
    for file in store_files:
        if file.get_name()[-3:] != "bag":
            continue

        if file.get_path() in trashed_bags_by_name:
            continue

        if not file.get_path() in bags_by_name:
            print("NEW: %s at %s" % (file.get_save_name(), file.get_path()))
            register_bag_file(api, store_info.name, file)

    print("Done!")