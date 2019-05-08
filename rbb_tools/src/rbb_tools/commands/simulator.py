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

import yaml

from rbb_tools.common.shell import Colors
from rbb_tools.simenvs.environment import SimulationEnvironment, import_simulation_environment


def simulate(configuration, output_dir, tmp_dir, no_color=False, identifier=None):
    logging.basicConfig(level=logging.INFO)

    if not tmp_dir:
        tmp_dir = os.getcwd() + "/temp"

    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    if not output_dir:
        output_dir = os.getcwd() + "/output"

    if not 'env' in configuration:
        logging.fatal("Simulation environment (env) not defined in configuration!")
        return False

    sim_env_module = import_simulation_environment(configuration['env'])

    if not 'env_config' in configuration:
        logging.fatal("Environment configuration (env_config) missing in configuration file!")
        return False

    if not 'sim_config' in configuration:
        logging.fatal("Simulation configuration (sim_config) missing in configuration file!")
        return False

    sim_env = sim_env_module(configuration['env_config'],
                             configuration['sim_config'],
                             output_dir,
                             tmp_dir)  # type: SimulationEnvironment

    manifest_path = output_dir + "/manifest.yaml"
    try:
        logging.info("Preparing simulation environment...")
        if not sim_env.prepare():
            logging.fatal("Preparation failed!")
            return False

        logging.info("Starting simulation.")
        if not sim_env.simulate():
            logging.fatal("Simulation failed!")
            return False
        else:
            logging.info("Simulation finished!")

        if not os.path.isfile(output_dir + "/output.yaml"):
            logging.fatal("Simulation results file is missing in output directory!")
        else:
            results = None
            with open(output_dir + "/output.yaml", 'r') as f:
                results = yaml.safe_load(f)

            manifest = {
                'server_info': {
                    'identifier': identifier
                },
                'bags': {},
                'runs': []
            }

            print("Simulation results of '%s'" % results['title'])
            fails = 0
            passes = 0
            for rep in results['repetitions']:
                run = results['repetitions'][rep]
                pass_fail = Colors.colorize("PASS", Colors.OKGREEN, no_color) if run['pass'] else Colors.colorize("FAIL", Colors.FAIL, no_color)
                print("[%s] '%s' in %.2f seconds" % (pass_fail, rep, run['duration']))

                bag = None
                if 'bag' in run and run['bag']:
                    bag_path = output_dir + "/" + run['bag']
                    if os.path.isfile(bag_path):
                        print(" - %s" % (run['bag']))
                        manifest['bags'][run['bag']] = True
                        bag = run['bag']
                    else:
                        manifest['bags'][run['bag']] = False
                        print(Colors.colorize(" - MISSING: %s" % (run['bag']), Colors.FAIL, no_color))

                if run['pass']:
                    passes += 1
                else:
                    fails += 1

                manifest['runs'].append({
                    'description': str(rep),
                    'duration': run['duration'],
                    'success': run['pass'],
                    'bag': bag,
                    'results': run['results'] if run['results'] else {}
                })

            print("%d fail(s), %d pass(es)" % (fails, passes))

            # TODO: Configurable criteria
            manifest['pass'] = fails == 0

            with open(manifest_path, 'w') as f:
                yaml.safe_dump(manifest, f, default_flow_style=False)

    except Exception:
        logging.exception("Exception while running simulation")
        return False
    finally:
        if sim_env:
            sim_env.clean()

    return manifest_path
