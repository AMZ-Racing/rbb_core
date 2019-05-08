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

from rbb_server.helper.permissions import has_permission, Permissions, hide
from sqlalchemy import *
from sqlalchemy.orm import relationship

from rbb_swagger_server.models import SimulationEnvironmentDetailed, SimulationEnvironmentSummary
from .base import Base


class SimulationEnvironment(Base):
    __tablename__ = "simulation_environment"
    uid = Column(Integer, primary_key=True)
    name = Column(String(200))
    module = Column(String(200))
    configuration = Column(JSON)
    example_configuration = Column(TEXT)
    rosbag_store_id = Column(Integer, ForeignKey('rosbag_store.uid'))

    # Relationship
    rosbag_store = relationship("RosbagStore")
    simulations = relationship("Simulation", cascade="all, delete-orphan")

    def to_swagger_model_summary(self, model=None, user=None):
        if model is None:
            model = SimulationEnvironmentSummary()

        model.detail_type = "SimulationEnvironmentSummary"
        model.name = self.name
        model.module_name = self.module

        if self.rosbag_store_id:
            model.rosbag_store = self.rosbag_store.name

        return model

    def to_swagger_model_detailed(self, user=None):
        model = self.to_swagger_model_summary(SimulationEnvironmentDetailed(), user=user)

        model.detail_type = "SimulationEnvironmentDetailed"
        model.config=hide(self.configuration, user, Permissions.SimulationEnvironmentConfigurationAccess, {"_hidden": True})
        model.example_config=self.example_configuration

        return model

    def from_swagger_model(self, api_model, user=None):
        model = api_model  # type: SimulationEnvironmentDetailed
        self.name = model.name
        self.module = model.module_name
        if has_permission(user, Permissions.SimulationEnvironmentConfigurationAccess):
            self.configuration = model.config
        self.example_configuration = model.example_config

        return model
