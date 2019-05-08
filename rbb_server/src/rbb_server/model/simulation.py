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

from rbb_swagger_server.models import SimulationDetailed, SimulationSummary
from .base import Base


class Simulation(Base):
    __tablename__ = "simulation"
    uid = Column(Integer, primary_key=True)
    description = Column(String(200))
    created = Column(DateTime(), server_default="now() AT TIME ZONE 'utc'")
    configuration = Column(JSON)
    result = Column(Integer)
    environment_id = Column(Integer, ForeignKey('simulation_environment.uid'))
    task_in_queue_id = Column(Integer, ForeignKey('task_queue.uid'))
    on_complete = Column(JSON)

    # Relationship
    environment = relationship("SimulationEnvironment", back_populates="simulations")
    task_in_queue = relationship("Task")
    runs = relationship("SimulationRun", cascade="all, delete-orphan")

    def to_swagger_model_summary(self, model=None, user=None):
        if model is None:
            model = SimulationSummary()

        model.detail_type = "SimulationSummary"
        model.identifier = self.uid
        model.description = self.description
        model.created = self.created
        model.result = self.result
        model.environment_name = self.environment.name

        if self.task_in_queue_id:
            model.queued_task_identifier = str(self.task_in_queue_id)
            model.queued_task_state = self.task_in_queue.state
        else:
            model._queued_task_identifier = ""

        return model

    def to_swagger_model_detailed(self, user=None, expand=False):
        model = self.to_swagger_model_summary(SimulationDetailed(), user=user)

        model.detail_type = "SimulationDetailed"
        model.config = self.configuration
        model.on_complete_action = self.on_complete

        if expand:
            model.environment = self.environment.to_swagger_model_detailed(user=user)
            model.runs = [x.to_swagger_model_detailed(user=user) for x in self.runs]
            if self.task_in_queue_id:
                model.queued_task = self.task_in_queue.to_swagger_model_detailed(user=user)
            else:
                model.queued_task = None

        return model

    def from_swagger_model(self, api_model, user=None):
        model = api_model  # type: SimulationDetailed
        self.description = model.description
        self.created = model.created.replace(tzinfo=None)
        self.result = model.result
        self.configuration = model.config
        self.on_complete = model.on_complete_action

        if model.queued_task_identifier:
            self.task_in_queue_id = int(model.queued_task_identifier)
        else:
            self.task_in_queue_id = None