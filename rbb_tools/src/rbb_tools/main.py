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

import argparse
import os
import platform

import rbb_client
from rbb_client.models.file_store import FileStore
from rbb_storage import *
from rbb_tools.extraction.extractor import Extractor
from rbb_tools.common.storage import Storage


api_host = "http://localhost:8080/api/v0"
if 'RBB_URL' in os.environ:
    api_host = os.environ['RBB_URL']

api_key = ""
if 'RBB_KEY' in os.environ:
    api_key = os.environ['RBB_KEY']

api_username = ""
if 'RBB_USER' in os.environ:
    api_username = os.environ['RBB_USER']

api_password = ""
if 'RBB_PASS' in os.environ:
    api_password = os.environ['RBB_PASS']

config_file = ""
if 'RBB_CONFIG_FILE' in os.environ:
    config_file = os.environ['RBB_CONFIG_FILE']
else:
    config_file = os.path.expanduser("~/.rbb/config")


def get_api():
    if api_key != "":
        rbb_client.configuration.use_bearer_auth = True
        rbb_client.configuration.token = api_key
    else:
        rbb_client.configuration.use_bearer_auth = False
        rbb_client.configuration.username = api_username
        rbb_client.configuration.password = api_password

    api_instance = rbb_client.BasicApi(rbb_client.ApiClient(host=api_host))
    Storage.initialize(api_instance)
    return api_instance


def get_file_store(store_name, api):
    store = api.get_file_store(store_name)  # type: FileStore
    return Storage.factory(store.name, store.store_type, store.store_data)


def stores_index_cmd(args):
    import rbb_tools.commands.index
    rbb_tools.commands.index.command(args.store_name, get_api())


def stores_list_cmd(args):
    import rbb_tools.commands.stores
    rbb_tools.commands.stores.list(get_api())


def stores_add_cmd(args):
    import rbb_tools.commands.stores
    rbb_tools.commands.stores.create(get_api(), args.store_name, args.description,
                                     args.store_type, args.default_file_store, args.options)


def bags_list_cmd(args):
    import rbb_tools.commands.bags
    rbb_tools.commands.bags.command(args.store_name, get_api())


def bags_upload_manifest_cmd(args):
    import rbb_tools.commands.upload
    rbb_tools.commands.upload.command(args.manifest, args.file_store, get_api())


def bags_download_cmd(args):
    import rbb_tools.commands.download
    rbb_tools.commands.download.command(args.store_name, args.bag_name, get_api())


def bags_process_cmd(args):
    import rbb_tools.commands.stores
    rules = []

    if args.rules:
        rules = [x.strip() for x in args.rules.split(",")]


    rbb_tools.commands.stores.process_single_bag(get_api(),
                                      args.store_name,
                                      args.bag_name,
                                      [args.configuration],
                                      args.tmp_dir,
                                      args.output_dir,
                                      rules,
                                      args.no_clean)

def config_download_cmd(args):
    import rbb_tools.commands.config

    rbb_tools.commands.config.download(get_api(), args.config_name, args.target_directory, no_clean=args.no_clean, tmp_dir=args.tmp_dir);


def config_list_cmd(args):
    import rbb_tools.commands.config

    rbb_tools.commands.config.list(get_api())


def stores_process_cmd(args):
    import rbb_tools.commands.stores
    rules = []

    if args.rules:
        rules = [x.strip() for x in args.rules.split(",")]

    configurations = []
    if args.configuration != "auto":
        configurations = [args.configuration]

    rbb_tools.commands.stores.process_store(get_api(),
                                      args.store_name,
                                      configurations,
                                      args.tmp_dir,
                                      args.output_dir,
                                      rules,
                                      args.no_clean)


def extract_cmd(args):
    try:
        rules = []

        if args.rules:
            rules = [x.strip() for x in args.rules.split(",")]

        ex = Extractor(
            args.configuration,
            args.bag,
            args.tmp_dir,
            args.output_dir,
            args.dry_run,
            args.overwrite,
            rules)

    except RuntimeError as e:
        print("Error during initialization of the extractor!")
        print(e.message)
        return

    ex.run()


def simulator_run_cmd(args):
    import rbb_tools.commands.simulator
    import yaml

    config = None
    with open(args.config_path, 'r') as f:
        config = yaml.safe_load(f)

    rbb_tools.commands.simulator.simulate(config, args.output_dir, args.tmp_dir)


def simserver_upload_cmd(args):
    import rbb_tools.commands.simserver
    rbb_tools.commands.simserver.upload(get_api(), args.manifest, args.ros_bag_store)


def simserver_simulate_cmd(args):
    import rbb_tools.commands.simserver
    rbb_tools.commands.simserver.simulate(get_api(), args.identifier, args.output_dir, args.tmp_dir)


def simserver_save_env_cmd(args):
    import rbb_tools.commands.simserver
    import yaml
    config = None
    with open(args.config_file, 'r') as f:
        config = yaml.safe_load(f)
    rbb_tools.commands.simserver.save_env(get_api(), args.name, config, args.ros_bag_store)


def authorize_cmd(args):
    import rbb_tools.commands.auth

    global config_file
    key_file = config_file
    if args.key_file:
        key_file = args.key_file

    rbb_tools.commands.auth.authorize(get_api(), key_file)


def work_cmd(args):
    name = platform.node()
    if args.name:
        name = args.name

    import rbb_tools.commands.work
    rbb_tools.commands.work.work(get_api(), name, args.poll_period)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="rbbtools")
    parser.add_argument('-k', '--key', default="")
    parser.add_argument('-u', '--user', default="")
    parser.add_argument('-p', '--password', default="")
    parser.add_argument('-U', '--host-url', default="")
    parser.add_argument('-v', '--verbose', action="store_true", help="Print extra information")

    subparsers = parser.add_subparsers(title='Top level commands',
                                       description="[C/S] = Client/Server commands, [Loc] = Local commands",
                                       help='', metavar="<command>")

    ###############
    # Client/server commands

    ###
    # Bag commands
    ###

    bags_parser = subparsers.add_parser('bags', help="[C/S] Manage the bags inside a bag store")
    bags_subparsers = bags_parser.add_subparsers(title='Commands',
                                       description='valid commands',
                                       help='')

    bags_list_subparser = bags_subparsers.add_parser('list', help="List bags in store")
    bags_list_subparser.add_argument('store_name', type=str)
    bags_list_subparser.set_defaults(func=bags_list_cmd)

    bags_download_subparser = bags_subparsers.add_parser('download', help="Download a bag from the server")
    bags_download_subparser.add_argument('store_name', type=str)
    bags_download_subparser.add_argument('bag_name', type=str)
    bags_download_subparser.set_defaults(func=bags_download_cmd)

    bags_upload_manifest_subparser = bags_subparsers.add_parser('upload', help="Upload an extraction manifest to the server")
    bags_upload_manifest_subparser.add_argument('manifest', type=str)
    bags_upload_manifest_subparser.add_argument("--file-store", type=str, help="File store to use for storage of product files", default="")
    bags_upload_manifest_subparser.set_defaults(func=bags_upload_manifest_cmd)

    bag_process_subparser = bags_subparsers.add_parser('process', help="Download a bag, process it and upload the results")
    bag_process_subparser.add_argument('store_name', type=str)
    bag_process_subparser.add_argument('bag_name', type=str)
    bag_process_subparser.add_argument('configuration', type=str, help="Configuration file/directory/zip")
    bag_process_subparser.add_argument("--tmp-dir", help="Temporary storage directory", default="")
    bag_process_subparser.add_argument("--output-dir", help="Output directory", default="")
    bag_process_subparser.add_argument("--rules", help="Only run the specified rules, separated by commas", default="")
    bag_process_subparser.add_argument("--no-clean", action="store_true", help="Keep files/bags after processing")
    bag_process_subparser.set_defaults(func=bags_process_cmd)

    ###
    # Store commands
    ###

    stores_parser = subparsers.add_parser('stores', help="[C/S] Manage bag stores")
    stores_subparsers = stores_parser.add_subparsers(title='Commands',
                                       description='valid commands',
                                       help='')

    stores_add_subparser = stores_subparsers.add_parser('add', help="Add a new bag store")
    stores_add_subparser.add_argument('store_name', type=str)
    stores_add_subparser.add_argument('description', type=str)
    stores_add_subparser.add_argument('store_type', type=str)
    stores_add_subparser.add_argument('-f', '--default-file-store', type=str, default="")
    stores_add_subparser.add_argument('options', nargs=argparse.REMAINDER)
    stores_add_subparser.set_defaults(func=stores_add_cmd)

    stores_list_subparser = stores_subparsers.add_parser('list', help="List all bag stores")
    stores_list_subparser.set_defaults(func=stores_list_cmd)

    stores_index_subparser = stores_subparsers.add_parser('index', help="Discover bags in the underlying storage system")
    stores_index_subparser.add_argument('store_name', type=str)
    stores_index_subparser.set_defaults(func=stores_index_cmd)

    stores_process_subparser = stores_subparsers.add_parser('process', help="Process all bags in the store that do not have meta-available")
    stores_process_subparser.add_argument('store_name', type=str)
    stores_process_subparser.add_argument('configuration', type=str, help="Configuration file/directory/zip", default="auto")
    stores_process_subparser.add_argument("--tmp-dir", help="Temporary storage directory", default="")
    stores_process_subparser.add_argument("--output-dir", help="Output directory", default="")
    stores_process_subparser.add_argument("--rules", help="Only run the specified rules, separated by commas", default="")
    stores_process_subparser.add_argument("--no-clean", action="store_true", help="Keep files/bags after processing")
    stores_process_subparser.set_defaults(func=stores_process_cmd)

    ###
    # Config commands
    ###

    config_parser = subparsers.add_parser('config', help="[C/S] Manage extraction configurations")
    config_subparsers = config_parser.add_subparsers(title='Commands',
                                       description='valid commands',
                                       help='')

    config_list_subparser = config_subparsers.add_parser('list', help="List configurations")
    config_list_subparser.set_defaults(func=config_list_cmd)

    config_download_subparser = config_subparsers.add_parser('download', help="Download a configuration")
    config_download_subparser.add_argument('config_name', type=str)
    config_download_subparser.add_argument('target_directory', type=str)
    config_download_subparser.add_argument("--tmp-dir", help="Temporary storage directory", default="")
    config_download_subparser.add_argument("--no-clean", action="store_true", help="Keep files/bags after processing")
    config_download_subparser.set_defaults(func=config_download_cmd)

    ###
    # Simulation server commands
    ###

    simserver_parser = subparsers.add_parser('simserver', help="[C/S] Interact with the simulation server")
    simserver_subparsers = simserver_parser.add_subparsers(title='Commands',
                                       description='valid commands',
                                       help='')

    simserver_simulate_subparser = simserver_subparsers.add_parser('simulate',
                                                            help="Simulate a simulation job on this computer")
    simserver_simulate_subparser.add_argument('identifier', type=int)
    simserver_simulate_subparser.add_argument("--tmp-dir", help="Temporary storage directory", default="")
    simserver_simulate_subparser.add_argument("--output-dir", help="Output directory", default="")
    simserver_simulate_subparser.set_defaults(func=simserver_simulate_cmd)

    simserver_upload_subparser = simserver_subparsers.add_parser('upload', help="Upload a simulation manifest to the server")
    simserver_upload_subparser.add_argument('manifest', type=str)
    simserver_upload_subparser.add_argument("--ros-bag-store", type=str, help="Ros bag store to use for storage of bags", default="")
    simserver_upload_subparser.set_defaults(func=simserver_upload_cmd)

    simserver_upload_subparser = simserver_subparsers.add_parser('save-env', help="Create/update a simulation environment")
    simserver_upload_subparser.add_argument('name', type=str)
    simserver_upload_subparser.add_argument('config_file', type=str)
    simserver_upload_subparser.add_argument("--ros-bag-store", type=str, help="Ros bag store to use for storage of bags", default="")
    simserver_upload_subparser.set_defaults(func=simserver_save_env_cmd)

    ###
    # Authorize command
    ###

    auth_parser = subparsers.add_parser('authorize', help="[C/S] Write current url and session to config file")
    auth_parser.add_argument("--key-file", help="File to store the key (default is ~/.rbb/config)", default="")
    auth_parser.set_defaults(func=authorize_cmd)

    ###
    # Work command
    ###

    work_parser = subparsers.add_parser('work', help="[C/S] Run tasks in the work queue")
    work_parser.add_argument("--poll-period", help="Seconds to sleep between polls if no task available", type=int, default=60)
    work_parser.add_argument("--name", help="Name of this worker node", default="")
    work_parser.add_argument("--label", help="Node labels", default="")
    work_parser.set_defaults(func=work_cmd)

    ###############
    # Local commands

    ###
    # Simulator commands
    ###

    simulator_parser = subparsers.add_parser('simulator', help="[Loc] Run simulation environments locally")
    simulator_subparsers = simulator_parser.add_subparsers(title='Commands',
                                       description='valid commands',
                                       help='')

    simulator_run_subparser = simulator_subparsers.add_parser('run', help="Run a simulation environment")
    simulator_run_subparser.add_argument('config_path', type=str)
    simulator_run_subparser.add_argument("--tmp-dir", help="Temporary storage directory", default="")
    simulator_run_subparser.add_argument("--output-dir", help="Output directory", default="")
    simulator_run_subparser.set_defaults(func=simulator_run_cmd)

    ###
    # Manifest
    ###

    create_parser = subparsers.add_parser('extract', help="[Loc] Extract information products from a bag on your local filesystem")
    create_parser.add_argument('configuration', type=str, help="Configuration file/directory/zip", metavar="CONFIGURATION_FILE")
    create_parser.add_argument('bag', type=str, help="Bag file to extract", metavar="BAG_FILE")
    create_parser.add_argument("--tmp-dir", help="Temporary storage directory", default="")
    create_parser.add_argument("--output-dir", help="Output directory", default="")
    create_parser.add_argument("--rules", help="Only run the specified rules, separated by commas", default="")
    create_parser.add_argument("--dry-run", action="store_true",
                               help="Show extraction products without running the extraction")
    create_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing products")
    create_parser.set_defaults(func=extract_cmd)

    args = parser.parse_args()

    if args.key:
        api_key = args.key

    if args.user:
        api_username = args.user

    if args.password:
        api_password = args.password

    if args.host_url:
        api_host = args.host_url

    if not api_password and not api_username and not api_key:
        if os.path.isfile(config_file):
            print("Using config file (%s)." % config_file)

            with open(config_file, "r") as f:
                api_host = f.readline().strip()
                api_key = f.readline().strip()

    args.func(args)