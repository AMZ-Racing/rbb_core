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
import datetime
import json
import logging
import os

import yaml

import rbb_storage
import rbb_tools.commands.simulator
from rbb_tools.common.storage import Storage
from rbb_tools.hooks.simulation_finished_hook import SimulationFinishedHook
from rbb_client import SimulationDetailed, SimulationRunDetailed, BagStoreDetailed, BagDetailed, \
    SimulationEnvironmentDetailed
from rbb_client.apis.basic_api import BasicApi
from rbb_client.rest import ApiException
from rbb_client.rest import RESTClientObject
from rbb_tools.common import WorkingDirectory


def get_bag_store(api, store_name):
    store = api.get_store(store_name)  # type: BagStoreDetailed
    return Storage.factory(store.name, store.store_type, store.store_data)


def upload_bag(api, bag, store_name, sim_id, storage, progress_indicator=True):
    print("Uploading bag '%s'..." % (bag))

    file_name = os.path.basename(bag)

    file_data = storage.store_file(
        bag,
        "application/octet-stream",
        directory_hint= "simulation_%d" % sim_id,
        name_hint=file_name,
        progress_indicator=progress_indicator
    )

    bag = BagDetailed()
    bag.detail_type="BagDetailed"
    bag.name="sim_%d-%s" % (sim_id, file_name)
    bag.store_data=file_data
    bag.size=0
    bag.meta_available=False
    bag.discovered=datetime.datetime.utcnow()
    bag.is_extracted=False
    bag.comment=""
    bag.topics=[]
    bag.products=[]
    bag.extraction_failure = False

    return api.put_bag_meta(store_name, bag.name, bag)


def save_env(api, name, config, rosbag_store):
    api = api  # type: BasicApi

    env = None
    try:
        env = api.get_simulation_environment(name)  # type: SimulationEnvironmentDetailed
    except ApiException as e:
        if e.status == 404:
            env = SimulationEnvironmentDetailed()
            env.detail_type = "SimulationEnvironmentDetailed"
            env.rosbag_store = ""
            env.example_config = "# No example"
            env.name = name
        else:
            raise e

    if rosbag_store:
        if rosbag_store == "none":
            env.rosbag_store = ""
        else:
            env.rosbag_store = rosbag_store

    env.config = config['env_config']
    env.module_name = config['env']

    if 'example' in config:
        env.example_config = config['example']

    api.put_simulation_environment(name, env)


def simulate(api, identifier, output_dir="", tmp_dir=""):
    api = api  # type: BasicApi

    try:
        sim = api.get_simulation(identifier, expand=True)  # type: SimulationDetailed
    except Exception as e:
        logging.exception("Could not get the simulation job from the server!")
        return

    logging.info("Starting simulation #%d '%s' in environment '%s'..." %
                (sim.identifier, sim.description, sim.environment_name))

    tmp = WorkingDirectory(tmp_dir, "/temp", True)
    output = WorkingDirectory(output_dir, "/output")

    # Write the configuration file
    sim_config_file = {
        'env': sim.environment.module_name,
        'env_config': sim.environment.config,
        'sim_config': sim.config
    }

    with open(output.get_path('simulation_config.yaml'), 'w') as f:
        yaml.safe_dump(sim_config_file, f, default_flow_style=False)

    # Run the simulation
    manifest_path = rbb_tools.commands.simulator.simulate(
        sim_config_file,
        output.get_directory_path(),
        tmp.get_directory_path(),
        no_color=True,
        identifier=sim.identifier)

    tmp.clean()

    return manifest_path


def upload(api, manifest_path, bag_store_name="", progress_indicator=True):
    api = api  # type: BasicApi
    manifest = None

    if os.path.isdir(manifest_path):
        logging.fatal("Cannot upload a directory, please specify the manifest file!")
        return False

    with open(manifest_path, 'r') as stream:
        try:
            manifest = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logging.fatal("Invalid YAML in configuration file: %s" % str(exc))
            return False

    if not manifest:
        logging.fatal("Cannot load manifest file")
        return False

    if 'server_info' not in manifest:
        logging.fatal("Server info not in manifest")
        return False
    server_info = manifest['server_info']

    if 'identifier' not in server_info or not server_info['identifier']:
        logging.fatal("Server info not complete in manifest (identifier is needed)")
        return False

    identifier = server_info['identifier']
    manifest_dir = os.path.dirname(os.path.realpath(manifest_path))

    # Get simulation
    try:
        sim = api.get_simulation(identifier, expand=True)  # type: SimulationDetailed
    except Exception as e:
        logging.exception("Cannot access simulation job on server!")
        return False

    bag_store_name = bag_store_name if bag_store_name else sim.environment.rosbag_store
    bag_storage = None
    if bag_store_name:
        try:
            bag_storage = get_bag_store(api, bag_store_name)
            logging.info("Using bag store '%s'" % bag_store_name)
        except Exception as e:
            logging.exception("Cannot load bag store '%s'!" % bag_store_name)
            return False

    # Upload the bags
    uploaded_bags = {}
    for bag in manifest['bags']:
        try:
            uploaded_bags[bag] = False
            if not manifest['bags'][bag]:
                logging.info("Skipping unmarked bag '%s'" % bag)
            else:
                if bag_storage:
                    uploaded_bags[bag] = upload_bag(api,
                                                    manifest_dir + "/" + bag,
                                                    bag_store_name,
                                                    sim.identifier,
                                                    bag_storage,
                                                    progress_indicator)
        except:
            logging.exception("Uploading bag to server failed!")

    # Upload the runs
    for run in manifest['runs']:
        try:
            run_model = SimulationRunDetailed()
            run_model.identifier = 0
            run_model.detail_type = "SimulationRunDetailed"
            run_model.success = run['success']
            run_model.description = run['description']
            run_model.results = run['results']
            run_model.duration = run['duration']

            if run['bag'] in uploaded_bags and uploaded_bags[run['bag']]:
                bag = uploaded_bags[run['bag']]
                run_model.bag_store_name = bag_store_name
                run_model.bag_name = bag.name

            run_model = api.new_simulation_run(sim.identifier, run_model)
            logging.info("Successfully stored run '%s" % run_model.description)
        except:
            logging.exception("Uploading run '%s' failed!" % run['description'])

    # Fill in the simulation fields
    sim.result = 100 if manifest['pass'] else -100
    api.put_simulation(sim.identifier, sim)

    # Check if there are on complete actions
    #SimulationFinishedHook.trigger(api, sim, manifest)

    return True

