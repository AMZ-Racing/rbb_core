# Local RBB stack

This readme explains how to run a local RBB stack using a few docker containers.
The stack uses docker-compose to manage the individual containers.

*Tested on Ubuntu 16.04*

## Dependencies

- **RBB Web Interface**
    - Clone from https://bitbucket.org/amzracing/rosbag_bazaar_web
    - To build this you need [NodeJS v8+](https://nodejs.org/en/download/package-manager/#debian-and-ubuntu-based-linux-distributions-enterprise-linux-fedora-and-snap-packages) and [Yarn](https://yarnpkg.com/lang/en/docs/install/#debian-stable)
- **Docker** (tested with v18.06.1)  
    See https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-using-the-repository
- **Docker Compose** (tested with v1.23.1)  
    See https://docs.docker.com/compose/install/#install-compose
- **NVidia Docker runtime**  
    *This is required to have hardware accelerated OpenGL inside the containers*  
    See https://github.com/NVIDIA/nvidia-docker/blob/master/README.md

These are the only dependencies, everything else (e.g. ROS, Python, PostgreSQL, et..) is handled inside the containers.

## Build

The docker images for the API server and web interface can be built manually. This can be done with the `build-staging.sh` scripts in both repositories.

In the root of this repository run:  
`./build-containers.sh`

In the root of the web interface repository run:  
`./build-containers.sh`

All required docker images should now be available.

## Run

1. The worker containers need to access your host X server for hardware acceleration. To give them this access you need to execute:  
`xhost +local:root`
2. Now you can start up the local stack by executing the following command inside the *local-stack* folder:  
`docker-compose up`
3. You will see all containers booting up now. You might see some errors from the worker containers, because they cannot authenticate with the API server. This is not so important right now and a restart of the stack will solve this.
4. The web interface is available at [http://localhost](http://localhost)  
`Username: admin`  
`Password: admin`
5. The Minio interface is available at [http://localhost:9000](http://minio.ats.localhost:9000) with login MINIOKEY / MINIOSUPERSECRET
6. To stop the local stack run:  
`docker-compose stop`
7. To remove the local stack run (This will delete everything):  
`docker-compose down`