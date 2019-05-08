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

import yaml

from rbb_tools.simenvs.environment import SimulationEnvironment


class TestSimulationEnvironment(SimulationEnvironment):

    def __init__(self, env_config, sim_config, output_dir, tmp_dir):
        super(TestSimulationEnvironment, self).__init__(env_config, sim_config, output_dir, tmp_dir)

        self._fail = True

        if 'fail' in sim_config:
            self._fail = sim_config["fail"]

    def prepare(self):
        logging.info("TestSimulationEnvironment.prepare()")
        return True

    def simulate(self):
        logging.info("TestSimulationEnvironment.simulate()")

        output_file = {
            'title': "TestSimulationEnvironment",
            'repetitions': {
                'Test run 1': {
                    'bag': None,
                    'pass': True,
                    'duration': 1.0,
                    'results': {"some-result": "good"}
                },
                'Test run 2': {
                    'bag': 'missing-bag.bag',
                    'pass': not self._fail,
                    'duration': 1.0,
                    'results': {"some-result": "bad"}
                },
                'Test run 3': {
                    'bag': 'bag.bag',
                    'pass': True,
                    'duration': 1.0,
                    'results': {"some-result": "this one has a bag"}
                }
            }
        }

        with open(self._output_dir + "/output.yaml", 'w') as f:
            yaml.safe_dump(output_file, f, default_flow_style=False)

        with open(self._output_dir + "/bag.bag", 'w') as f:
            for x in range(1024):
                f.write("THIS IS A FAKE ROSBAG \n")

        return True

    def clean(self):
        logging.info("TestSimulationEnvironment.clean()")


environment = TestSimulationEnvironment

