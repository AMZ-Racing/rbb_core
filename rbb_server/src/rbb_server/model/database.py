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

from sqlalchemy import create_engine, engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.engine import url as engine_url
import os

# Models
from .base import Base
from .rosbag import Rosbag
from .rosbag_store import RosbagStore
from .rosbag_product import RosbagProduct
from .rosbag_product_topic import RosbagProductTopic
from .rosbag_topic import RosbagTopic
from .file import File
from .file_store import FileStore
from .rosbag_product_file import RosbagProductFile
from .session import Session
from .user import User
from .rosbag_extraction_configuration import RosbagExtractionConfiguration
from .task import Task
from .tag import Tag
from .simulation_environment import SimulationEnvironment
from .simulation import Simulation
from .simulation_run import SimulationRun
from .rosbag_comment import RosbagComment
from .permission import Permission
from .config_key_value import ConfigKeyValue


class Database:
    _session = None
    _engine = None

    @staticmethod
    def get_session() -> scoped_session:
        return Database._session

    @staticmethod
    def get_engine() -> engine:
        return Database._engine

    @staticmethod
    def init(config=None, debug=False):
        db_url = {'drivername': 'postgres',
                  'username': os.getenv('RBB_DB_USER') if os.getenv('RBB_DB_USER') else 'postgres',
                  'password': os.getenv('RBB_DB_PASS') if os.getenv('RBB_DB_PASS') else 'postgres',
                  'host': os.getenv('RBB_DB_HOST') if os.getenv('RBB_DB_HOST') else 'localhost',
                  'port': os.getenv('RBB_DB_PORT') if os.getenv('RBB_DB_PORT') else 5432,
                  'database': os.getenv('RBB_DB_DB') if os.getenv('RBB_DB_DB') else 'postgres'}

        Database._engine = create_engine(engine_url.URL(**db_url), echo=debug, convert_unicode=True)
        db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=Database._engine))

        Base.query = db_session.query_property()
        Database._session = db_session

