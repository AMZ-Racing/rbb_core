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

from sqlalchemy import *
from sqlalchemy.orm import relationship

from rbb_swagger_server.models import SimulationRunSummary, SimulationRunDetailed
from .base import Base


class SimulationRun(Base):
    __tablename__ = "simulation_run"
    uid = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey('simulation.uid'))
    bag_id = Column(Integer, ForeignKey('rosbag.uid'))
    description = Column(String(200))
    success = Column(Boolean)
    duration = Column(Float)
    results = Column(JSON)

    # Relationship
    bag = relationship("Rosbag")
    simulation = relationship("Simulation", back_populates="runs")

    def to_swagger_model_summary(self, model=None, user=None):
        if model is None:
            model = SimulationRunSummary()

        model.detail_type = "SimulationRunSummary"
        model.identifier = self.uid
        model.success = self.success
        model.description = self.description
        model.duration = self.duration

        if self.bag_id:
            model.bag_name = self.bag.name
            model.bag_store_name = self.bag.store.name

        return model

    def to_swagger_model_detailed(self, user=None, expand=False):
        model = self.to_swagger_model_summary(SimulationRunDetailed(), user=user)

        model.detail_type = "SimulationRunDetailed"
        model.results = self.results

        if expand and self.bag:
            model.bag = self.bag.to_swagger_model_summary(user=user)

        return model

    def from_swagger_model(self, api_model, user=None):
        model = api_model  # type: SimulationRunDetailed
        self.description = model.description
        self.success = model.success
        self.duration = model.duration
        self.results = model.results

        return model
