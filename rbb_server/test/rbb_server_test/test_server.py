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

import connexion
from flask_cors import CORS

import rbb_server_test.database
from rbb_server.model.database import Database
from rbb_swagger_server.encoder import JSONEncoder


class TestConfig(object):
    DEBUG = True
    TESTING = True


def construct_test_server():
    # Setup the API Server
    app = connexion.App(__name__, specification_dir='./../../src/rbb_swagger_server/swagger/')
    app.app.json_encoder = JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'API to access the Rosbag Bazaar service'})

    # Setup link to the database and create new schema with fake data
    rbb_server_test.database.setup_database_for_test()

    # Enable debug
    app.app.config.from_object(TestConfig)

    @app.app.teardown_appcontext
    def shutdown_session(exception=None):
        Database.get_session().remove()

    # Allow requests from everywhere
    CORS(app.app)

    return app


if __name__ == '__main__':
    app = construct_test_server()
    app.run(host='127.0.0.1', port=8081, threaded=False)
