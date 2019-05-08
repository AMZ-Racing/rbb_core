#!/usr/bin/env bash

# Change working directory to script directory
cd $(dirname "$0")

# Download the swagger code generators
if [ ! -e swagger-codegen-cli-2.1.6.jar ]; then
    echo "swagger-codegen-cli-2-1-6.jar not found! Downloading it from maven.org..."
    wget http://central.maven.org/maven2/io/swagger/swagger-codegen-cli/2.1.6/swagger-codegen-cli-2.1.6.jar -O swagger-codegen-cli-2.1.6.jar
fi

if [ ! -e swagger-codegen-cli-2.3.1.jar ]; then
    echo "swagger-codegen-cli-2-3-1.jar not found! Downloading it from maven.org..."
    wget http://central.maven.org/maven2/io/swagger/swagger-codegen-cli/2.3.1/swagger-codegen-cli-2.3.1.jar -O swagger-codegen-cli-2.3.1.jar
fi

# Generate the code

# Typescript API
java -jar swagger-codegen-cli-2.3.1.jar generate -i ./top.yaml -l typescript-fetch -o ./generated/typescript-client -DmodelPropertyNaming=snake_case

# Python Server
java -jar swagger-codegen-cli-2.3.1.jar generate -i ./top.yaml -l python-flask -o ./generated/python-server -DpackageName=rbb_swagger_server

# Python Client
java -jar swagger-codegen-cli-2.1.6.jar generate -i ./top.yaml -l python -o ./generated/python-client -DpackageName=rbb_client