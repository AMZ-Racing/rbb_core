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

import connexion
from flask_cors import CORS
from werkzeug.contrib.fixers import ProxyFix

from rbb_server.model.database import Database
from rbb_swagger_server.encoder import JSONEncoder

##########################################################
# This is the startup for the gunicorn production server #
##########################################################

# Setup the API Server
app = connexion.App(__name__, specification_dir='./../rbb_swagger_server/swagger/')
app.app.json_encoder = JSONEncoder
app.add_api('swagger.yaml', swagger_ui=False, arguments={'title': 'API to access the Rosbag Bazaar service'})

# Initialize logging
logging.basicConfig(level=logging.INFO)

if "RBB_BEHIND_PROXY" in os.environ and os.environ["RBB_BEHIND_PROXY"]:
    logging.info("NOTE: Configured to run behind a proxy, disable if not the case!")
    # Fix proxy header
    app.app.wsgi_app = ProxyFix(app.app.wsgi_app)

# Setup link to the database
Database.init()

@app.app.teardown_appcontext
def shutdown_session(exception=None):
    Database.get_session().remove()

print("Running production server...")

# Allow requests from everywhere
CORS(app.app)