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
import os.path

from rbb_server.model.database import Database


def init_database_connection_for_test():
    Database._session = None
    Database._engine = None
    Database.init(debug=False)
    Database.get_session().execute("SET search_path TO unittest")


def close_database():
    Database._session.close()
    Database._engine.dispose()
    Database._session = None
    Database._engine = None


def setup_database_for_test():
    Database.init(debug=True)

    engine = Database.get_engine()
    connection = engine.connect()
    connection.execute("DROP SCHEMA IF EXISTS unittest CASCADE")
    connection.execute("CREATE SCHEMA unittest")
    connection.execute("SET search_path TO unittest, public")

    tx = connection.begin()
    try:
        # Create fresh schema
        with open(os.path.dirname(__file__) + "/../../src/rbb_server/schema.sql", 'r') as sql_file:
            sql = sql_file.read()
        connection.execute(sql)

        # Insert all our testing data
        with open(os.path.dirname(__file__) + "/test-data.sql", 'r') as sql_file:
            sql = sql_file.read()

        statements = sql.split(";")
        for statement in statements:
            sql = statement.strip()
            if sql:
                connection.execute(sql)

        tx.commit()
    except Exception as e:
        tx.rollback()
        logging.error(e)
        print("ERROR: Cannot load unittest data into database!")
        raise e

    connection.close()

    # Make current session use the testing schema
    Database.get_session().execute("SET search_path TO unittest")



