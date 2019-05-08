# Rosbag Bazaar API Server

The bazaar API server is the central core of the rosbag bazaar. All information about rosbags, 
their contents and their location is stored here. It is made accessible to all other services requiring 
this information using a "standard" API. The API is documented in swagger/openAPI format and can be 
found in the `/openapi` folder. A server stub is generated from this specification and is stored in 
the `/rbb_server/src/rbb_swagger_server` folder. Do not modify anything in this folder because if we update the specification
we want to be able to just copy a newly generated server stub there. 
The custom non-generated code is in the `/rbb_server/src/rbb_server` folder.

## Requirements
Python 3.5.2+

## Usage
The server can either be run by executing `rbb_server` as a module:

`/usr/bin/python3.5 -m rbb_server`

This will use the flasks built-in server. Or, the server can be run in production mode using gunicorn
as the WSGI server. Use the `/rbb_server/run-server` script for that.

## Testing server
To run the testing server, please execute the script in `bazaar_test/test_server.py`. This will
create a new `unittest` schema in the database filled with the data in `bazaar_test/test-data.sql`. It
can be reached here:

```
http://localhost:8081/api/v0
```