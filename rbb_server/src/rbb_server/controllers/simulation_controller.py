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
import logging

import connexion
import rbb_server.helper.auth as auth
import rbb_server.helper.database as db_helper
from rbb_server.helper.permissions import Permissions
from rbb_server.helper.error import handle_exception
from sqlalchemy import and_
from sqlalchemy.orm import Query

from rbb_server import Database
from rbb_server.model.database import SimulationEnvironment, Simulation, SimulationRun, Rosbag, RosbagStore
from rbb_server.model.task import Task, TaskState
from rbb_server.hooks.new_simulation_hook import NewSimulationHook
from rbb_swagger_server.models import SimulationRunDetailed, SimulationDetailed, SimulationEnvironmentDetailed
from rbb_swagger_server.models.error import Error


@auth.requires_auth_with_permission(Permissions.SimulationRead)
def get_simulation(sim_identifier, expand=None, user=None):  # noqa: E501
    """Get simulation

     # noqa: E501

    :param sim_identifier:
    :type sim_identifier: int
    :param expand:
    :type expand: bool

    :rtype: SimulationDetailed
    """
    try:
        session = Database.get_session()

        q = session.query(Simulation).filter(Simulation.uid == sim_identifier)  # type: Query
        model = q.first()
        if model:
            return model.to_swagger_model_detailed(user=user, expand=expand)
        else:
            return Error(code=404, message="Simulation not found"), 404

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.SimulationEnvironmentRead)
def get_simulation_environment(env_name, user=None):  # noqa: E501
    """Get simulation environment

     # noqa: E501

    :param env_name: Name of the simulation environment
    :type env_name: str

    :rtype: SimulationEnvironmentDetailed
    """
    try:
        session = Database.get_session()

        q = session.query(SimulationEnvironment).filter(SimulationEnvironment.name == env_name)  # type: Query
        model = q.first()
        if model:
            return model.to_swagger_model_detailed(user=user)
        else:
            return Error(code=404, message="Simulation environment not found"), 404

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.SimulationRead)
def get_simulation_run(sim_identifier, run_identifier, expand=None, user=None):  # noqa: E501
    """Get simulation run

     # noqa: E501

    :param sim_identifier:
    :type sim_identifier: int
    :param run_identifier:
    :type run_identifier: int
    :param expand:
    :type expand: bool

    :rtype: SimulationRunDetailed
    """
    try:
        session = Database.get_session()

        q = session.query(SimulationRun).filter(SimulationRun.uid == run_identifier)  # type: Query
        model = q.first()

        if model and model.simulation_id == sim_identifier:
            return model.to_swagger_model_detailed(user=user, expand=expand)
        else:
            return Error(code=404, message="Simulation run not found"), 404

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.SimulationEnvironmentRead)
def list_simulation_environments(user=None):
    """List available simulation environments

     # noqa: E501


    :rtype: List[SimulationEnvironmentSummary]
    """
    try:
        session = Database.get_session()
        q = session.query(SimulationEnvironment) #type: Query
        return [p.to_swagger_model_summary(user=user) for p in q]

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.SimulationRead)
def list_simulation_runs(sim_identifier, user=None):  # noqa: E501
    """List simulation runs

     # noqa: E501

    :param sim_identifier:
    :type sim_identifier: int

    :rtype: List[SimulationRunSummary]
    """
    try:
        session = Database.get_session()

        q = session.query(Simulation).filter(Simulation.uid == sim_identifier)  # type: Query
        model = q.first()
        if model:
            return [p.to_swagger_model_summary(user=user) for p in model.runs]
        else:
            return Error(code=404, message="Simulation not found"), 404

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.SimulationRead)
def list_simulations(limit=None, offset=None, ordering=None, user=None):  # noqa: E501
    """List simulations

     # noqa: E501


    :rtype: List[SimulationSummary]
    """
    try:
        session = Database.get_session()
        q = session.query(Simulation) #type: Query

        q = db_helper.query_pagination_ordering(q, offset, limit, ordering, {
            'created': Simulation.created,
            'identifier': Simulation.uid
        })

        return [p.to_swagger_model_summary(user=user) for p in q]

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.SimulationWrite)
def new_simulation(simulation, trigger=None, user=None):  # noqa: E501
    """New simulation

     # noqa: E501

    :param simulation: Simulation
    :type simulation: dict | bytes

    :rtype: SimulationDetailed
    """
    try:
        if connexion.request.is_json:
            simulation = SimulationDetailed.from_dict(connexion.request.get_json())  # noqa: E501

        session = Database.get_session()

        q = session.query(SimulationEnvironment).filter(SimulationEnvironment.name == simulation.environment_name)
        if not q.first():
            return Error(code=400, message="Simulation environment '%s' not found" % simulation.environment_name), 400

        model = Simulation()
        model.from_swagger_model(simulation, user=user)
        model.environment_id = q.first().uid
        model.uid = None
        session.add(model)
        session.commit()

        # Return a fresh copy from the DB
        q = session.query(Simulation).filter(Simulation.uid == model.uid)
        m = NewSimulationHook.trigger(q.first(), session, trigger, user)


        return m.to_swagger_model_detailed(user=user), 200

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.SimulationWrite)
def new_simulation_run(sim_identifier, simulation_run, user=None):  # noqa: E501
    """New simulation run

     # noqa: E501

    :param sim_identifier:
    :type sim_identifier: int
    :param simulation_run: Simulation run
    :type simulation_run: dict | bytes

    :rtype: SimulationRunDetailed
    """
    try:
        if connexion.request.is_json:
            simulation_run = SimulationRunDetailed.from_dict(connexion.request.get_json())  # noqa: E501

        session = Database.get_session()

        # Find the simulation
        q = session.query(Simulation).filter(Simulation.uid == sim_identifier)
        simulation = q.first()
        if not simulation:
            return Error(code=404, message="Simulation not found"), 404

        model = SimulationRun()
        model.from_swagger_model(simulation_run, user=user)
        model.simulation_id = simulation.uid

        if simulation_run.bag_store_name and simulation_run.bag_name:
            # Find the bag of the run
            q = session.query(Rosbag).filter(
                and_(RosbagStore.name == simulation_run.bag_store_name, Rosbag.name == simulation_run.bag_name)
            )
            bag = q.first()
            if not bag:
                return Error(code=400, message="Bag not found"), 400
            model.bag_id = bag.uid

        model.uid = None
        session.add(model)
        session.commit()

        # Return a fresh copy from the DB
        q = session.query(SimulationRun).filter(SimulationRun.uid == model.uid)
        return q.first().to_swagger_model_detailed(user=user), 200

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.SimulationWrite)
def put_simulation(sim_identifier, simulation, user=None):  # noqa: E501
    """Update a simulation

     # noqa: E501

    :param sim_identifier:
    :type sim_identifier: int
    :param simulation: Simulation
    :type simulation: dict | bytes

    :rtype: SimulationDetailed
    """
    try:
        if connexion.request.is_json:
            simulation = SimulationDetailed.from_dict(connexion.request.get_json())  # noqa: E501

        if simulation.identifier != sim_identifier:
            return Error(code=400, message="Body and path identifier are not the same"), 400

        session = Database.get_session()
        q = session.query(Simulation).filter(Simulation.uid == sim_identifier)
        model = q.first()
        if not model:
            return Error(code=404, message="Simulation not found"), 404

        q = session.query(SimulationEnvironment).filter(SimulationEnvironment.name == simulation.environment_name)
        if not q.first():
            return Error(code=400, message="Simulation environment '%s' not found" % simulation.environment_name), 400

        model.from_swagger_model(simulation, user=user)
        model.environment_id = q.first().uid
        session.commit()

        # Return a fresh copy from the DB
        q = session.query(Simulation).filter(Simulation.uid == model.uid)
        return q.first().to_swagger_model_detailed(user=user), 200

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.SimulationEnvironmentWrite)
def put_simulation_environment(env_name, environment, block_on_existing=None, user=None):  # noqa: E501
    """Create/update a simulation environment

     # noqa: E501

    :param env_name: Name of the simulation environment
    :type env_name: str
    :param environment: Simulation environment
    :type environment: dict | bytes

    :rtype: SimulationEnvironmentDetailed
    """
    try:
        if connexion.request.is_json:
            environment = SimulationEnvironmentDetailed.from_dict(connexion.request.get_json())  # noqa: E501

        session = Database.get_session()
        q = session.query(SimulationEnvironment).filter(SimulationEnvironment.name == env_name)  # type: Query

        model = SimulationEnvironment()
        if q.count() == 1:
            if block_on_existing:
                return Error(code=1000, message="Already exists."), 400

            model = q.first()
        else:
            if environment.name != env_name:
                return Error(code=400, message="Path and body tag have to be equal for a new environment"), 400
            session.add(model)

        model.from_swagger_model(environment, user=user)

        if environment.rosbag_store:
            q = session.query(RosbagStore).filter(RosbagStore.name == environment.rosbag_store)  # type: Query
            rosbag_store = q.first()
            if not rosbag_store:
                return Error(code=400, message="Rosbag store not found"), 400
            model.rosbag_store_id = rosbag_store.uid


        session.commit()
        return model.to_swagger_model_detailed(user=user)

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.SimulationWrite)
def delete_simulation(sim_identifier, user=None):  # noqa: E501
    """Delete simulation

     # noqa: E501

    :param sim_identifier:
    :type sim_identifier: int

    :rtype: None
    """
    session = Database.get_session()
    try:
        # Check the store
        q = session.query(Simulation).filter(Simulation.uid == sim_identifier)  # type: Query
        if q.first():
            session.delete(q.first())
            session.commit()
            return "", 204
        else:
            return Error(code=404, message="Simulation not found"), 404

    except Exception as e:
        logging.exception("Simulation deletion failed")
        session.rollback()

    return Error(code=500, message="Exception occurred"), 500


@auth.requires_auth_with_permission(Permissions.SimulationEnvironmentWrite)
def delete_simulation_environment(env_name, user=None):  # noqa: E501
    """Delete simulation

     # noqa: E501

    :param env_name: Name of the simulation environment
    :type env_name: str

    :rtype: None
    """
    session = Database.get_session()
    try:
        # Check the store
        q = session.query(SimulationEnvironment).filter(SimulationEnvironment.name == env_name)  # type: Query
        if q.first():
            session.delete(q.first())
            session.commit()
            return "", 204
        else:
            return Error(code=404, message="Simulation environment not found"), 404

    except Exception as e:
        logging.exception("Simulation environment deletion failed")
        session.rollback()

    return Error(code=500, message="Exception occurred"), 500