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

from rbb_client.api_client import ApiException
from rbb_client.models import SimulationEnvironmentDetailed, SimulationDetailed
from rbb_server_test import ClientServerBaseTestCase


class TestSimulation(ClientServerBaseTestCase):

    def test_delete_simulation(self):
        api = self.get_admin_api()

        sim = api.get_simulation(5)
        self.assertEqual(sim.description, "Test delete simulation")

        api.delete_simulation(5)
        try:
            sim = api.get_simulation(5)
            self.fail("Exception should be thrown")
        except ApiException as e:
            self.assertEqual(e.status, 404)

    def test_delete_simulation_environment(self):
        api = self.get_admin_api()

        env = SimulationEnvironmentDetailed()
        env.detail_type = "SimulationEnvironmentDetailed"
        env.name = "delete-test"
        env.module_name = "something"
        env.rosbag_store = None
        env.config = {}
        env.example_config = ""

        api.put_simulation_environment(env.name, env)

        sim = SimulationDetailed()
        sim.identifier = 0
        sim.detail_type = "SimulationDetailed"
        sim.environment_name = env.name
        sim.description = "test"
        sim.config = {}
        sim.created = datetime.datetime.now()
        sim.result = 0

        api.new_simulation(sim)

        api.delete_simulation_environment(env.name)
        try:
            sim = api.get_simulation_environment(env.name)
            self.fail("Exception should be thrown")
        except ApiException as e:
            self.assertEqual(e.status, 404)








