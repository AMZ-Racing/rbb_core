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

import importlib
import logging


class SimulationEnvironmentNotFound(RuntimeError):
    pass


class SimulationEnvironmentInvalidClass(RuntimeError):
    pass


def import_simulation_environment(module_name):
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        logging.exception("Could not load simulation environment module '%s'" % module_name)
        raise SimulationEnvironmentNotFound()

    if not issubclass(module.environment, SimulationEnvironment):
        raise SimulationEnvironmentInvalidClass()

    return module.environment


class SimulationEnvironment(object):

    def __init__(self, env_config, sim_config, output_dir, tmp_dir):
        self._output_dir = output_dir
        self._tmp_dir = tmp_dir

    def prepare(self):
        raise NotImplementedError()

    def simulate(self):
        raise NotImplementedError()

    def clean(self):
        raise NotImplementedError()