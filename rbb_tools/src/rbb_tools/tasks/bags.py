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
import shutil
import signal
import sys

from rbb_client import BasicApi
from rbb_tools.commands import index as index_command
from rbb_tools.commands.config import download as download_config
from rbb_tools.commands.download import command as download_bag
from rbb_tools.commands.upload import command as upload_bag_meta
from rbb_tools.common import WorkingDirectory
from rbb_tools.common.logging import Logger
from rbb_tools.extraction.extractor import Extractor
from rbb_tools.tasks import InvalidTaskConfiguration


def index(config, api):
    if 'store' not in config:
        raise InvalidTaskConfiguration()

    # TODO: Configuration can not be set now, the server always queues the auto extraction
    if 'configuration' not in config:
        raise InvalidTaskConfiguration()

    logging.getLogger().addHandler(logging.StreamHandler())

    index_command.command(config['store'], api)

    print("Done!")


def extraction_sigterm_handler(signal, frame):
    print("[SIGTERM] Received SIGTERM, exiting task...")
    sys.exit(1)
    pass


def extract(config, api):
    api = api  # type: BasicApi
    if 'store' not in config:
        raise InvalidTaskConfiguration()
    if 'configuration' not in config:
        raise InvalidTaskConfiguration()
    if 'bag' not in config:
        raise InvalidTaskConfiguration()

    logging.getLogger().addHandler(logging.StreamHandler())
    signal.signal(signal.SIGTERM, extraction_sigterm_handler)

    store_name = config['store']
    configuration_name = config['configuration']
    bag_name = config['bag']

    tmp_dir = WorkingDirectory("", "/ex_temp", True)
    cache_dir = WorkingDirectory("", "/ex_cache")
    output_dir = WorkingDirectory("", "/ex_output", True)

    configurations = []
    if configuration_name == "auto":
        configurations = api.get_store_extraction_configs(store_name)
    else:
        configurations = [api.get_extraction_config(configuration_name)]

    if len(configurations) == 0:
        logging.fatal("No configurations to use for extraction!")
        api.patch_bag_meta(store_name, bag_name, {'extraction_failure': True})
        exit(1)

    logging.info("Downloading/updating configurations...")

    configurations_files = []
    for config in configurations:
        try:
            config_path = os.path.realpath(tmp_dir.get_path("config/" + config.name))
            logging.info("Downloading config '%s' from server -> %s" % (config.name, config_path))

            # Clear the target path for the configuration
            if os.path.exists(config_path):
                shutil.rmtree(config_path)
            os.makedirs(config_path)

            # Get the configuration
            if download_config(api, config.name, config_path, tmp_dir=cache_dir.get_directory_path(), no_clean=True):
                configurations_files.append(config_path + "/config.yaml")
            else:
                logging.fatal("Downloading of config '%s' failed" % config.name)
        except:
            logging.exception("Could not download config '%s'" % config.name)

    if len(configurations_files) == 0:
        logging.fatal("Could not download any of the configurations!")
        exit(1)

    temporary_bag_name = os.path.realpath(tmp_dir.get_path(bag_name))

    # Download
    download_bag(store_name, bag_name, api, save_name=temporary_bag_name, progress_indicator=False)

    failure = False
    for configuration in configurations_files:
        try:
            # Process
            extraction_tmp_path = tmp_dir.get_path("extractor_temp")
            os.makedirs(extraction_tmp_path)

            ex = Extractor(
                configuration,
                temporary_bag_name,
                extraction_tmp_path,
                output_dir.get_directory_path(),
                False,
                True,
                [], Logger(debug=False))
            ex.run()

            manifest_path = os.path.realpath(output_dir.get_path("manifest.yaml"))
            ex.write_manifest(manifest_path, {
                    'server_url': api.api_client.host,
                    'store_name': store_name,
                    'bag_name': bag_name,
                })

            # Upload
            upload_bag_meta(manifest_path, "", api, progress_indicator=False)

            # Empty temporary dir
            shutil.rmtree(extraction_tmp_path)
        except:
            logging.exception("Exception while extracting with config '%s'" % configuration)
            failure = True

    tmp_dir.clean()
    output_dir.clean()

    if failure:
        api.patch_bag_meta(store_name, bag_name, {'extraction_failure': True})
        exit(1)

    exit(0)