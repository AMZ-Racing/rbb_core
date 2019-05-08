#!/usr/bin/env python3
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

# This script helps in moving bags from one store to another.
# The bags are matched to each other based on their base filename (xxx.bag)

import argparse
import logging

from rbb_server.model.database import Database, RosbagStore, Rosbag
from rbb_storage import Storage

logging.basicConfig(level=logging.INFO)
# Connection parameters are read from environment variables
Database.init()


def read_bags_into_map(store, plugin):
    bags = {}
    bags_full_path = {}
    q = Database.get_session().query(Rosbag).filter(Rosbag.store_id == store.uid)
    for bag in q:
        file_info = plugin.list_file(bag.store_data)
        bag_basename = file_info.get_name()
        bag_fullname = file_info.get_path()

        if bag_basename in bags:
            logging.warning("Duplicate bag '{}' in store '{}'".format(bag_basename, store.name))

        bags[bag_basename] = bag
        bags_full_path[bag_fullname] = bag

    return bags, bags_full_path


def do_move(arguments):
    q = Database.get_session().query(RosbagStore).filter(RosbagStore.name == args.source_store)
    source_store = q.first()
    if not source_store:
        logging.fatal("Cannot find source store with name {}".format(args.source_store))
        return False
    logging.info("Using source store {} with id {}".format(source_store.name, source_store.uid))
    source_store_plugin = Storage.factory(source_store.name, source_store.store_type, source_store.store_data)

    q = Database.get_session().query(RosbagStore).filter(RosbagStore.name == args.target_store)
    target_store = q.first()
    if not target_store:
        logging.fatal("Cannot find target store with name {}".format(args.target_store))
        return False
    logging.info("Using target store {} with id {}".format(target_store.name, target_store.uid))
    target_store_plugin = Storage.factory(target_store.name, target_store.store_type, target_store.store_data)

    source_bags, source_bags_path = read_bags_into_map(source_store, source_store_plugin)
    target_bags, target_bags_path = read_bags_into_map(target_store, target_store_plugin)

    store_files = target_store_plugin.list_files()
    move_files = []
    for file in store_files:
        if file.get_path()[-3:] == 'log':
            continue

        if file.get_path() in target_bags_path:
            logging.debug("{} SKIPPING already in target".format(file.get_path()))
            continue

        if file.get_name() in source_bags:
            logging.debug("{} MOVABLE".format(file.get_path()))
            old_file_data = source_store_plugin.list_file(source_bags[file.get_name()].store_data)
            move_files.append({
                'bag': source_bags[file.get_name()],
                'old_file_data': old_file_data,
                'new_file_data': file
            })
        else:
            logging.debug("{} NEW".format(file.get_path()))

    logging.info("PATH IN OLD STORE -> PATH IN NEW STORE")

    for move_file in move_files:
        logging.info("{} -> {}".format(move_file['old_file_data'].get_path(), move_file['new_file_data'].get_path()))

        bag = move_file['bag']
        file = move_file['new_file_data']

        if not arguments.dry_run:
            # Rename the bag and link it to the new file
            bag.name = file.get_save_name()
            bag.store_data = file.get_data()
            bag.store_id = target_store.uid

    if not arguments.dry_run:
        Database.get_session().commit()
        logging.info("FINISHED MOVING OF BAGS")
    else:
        logging.info("FINISHED DRY RUN")

parser = argparse.ArgumentParser(prog="rbbtools")
parser.add_argument('source_store', type=str, help="Name of the source copy store", metavar="SOURCE_STORE_NAME")
parser.add_argument('target_store', type=str, help="Name of the target copy store", metavar="TARGET_STORE_NAME")
parser.add_argument('-d', '--dry-run', action="store_true", help="Only show matches. No writing to database")
args = parser.parse_args()

do_move(args)
