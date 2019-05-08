# API Specification

This directory contains the API specification in `top.yaml`. It can be compiled into the libraries for each language using the `generate.sh` script.

## Remarks

The swagger codegenerators are not really stable and not all versions are compatible with the rest of the codebase. 
The following versions of the swagger codegenerator are used:

* Python client: 2.1.6 (python, -DpackageName=rbb_client, custom configuration.py see `rbb_client/src/rbb_client/configuration.mod.py`)
* Python server: 2.3.1 (python-flask, -DpackageName=rbb_swagger_server, no special changes needed)
* Typescript client: 2.3.1 (typescript-fetch, -DmodelPropertyNaming=snake_case, edit api.ts to use isomorphic-fetch)
