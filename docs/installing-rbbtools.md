# Installing rbbtools

rbbtools is the commandline tool of the rosbag bazaar. All functionality is build into 
this tool. Currently there is no *real* installation process yet. This means that you will have
to manually clone this repo and install the dependencies.

## Running

The main script is `/rbb_tools/rbbtools`, for an overview of the commands run:

`rbbtools -h`

## Dependencies

#### Required

* ROS (desktop, tested with kinetic)
* Python 2.7 (The one from ros ;)

#### Optional (only for recording RViz)

* Xephyr (sudo apt-get install xserver-xephyr)
* Xvfb (sudo apt-get install xvfb)
* xdotool (sudo apt-get install xdotool)
* ffmpeg (sudo apt-get install ffmpeg)
* VirtualGL (tested with 2.5.2)
    + Download deb package (https://sourceforge.net/projects/virtualgl/files/2.5.2/virtualgl_2.5.2_amd64.deb/download)
    + Install package with `sudo dpkg -i NAME_OF_THE_DEB_FILE`

#### Optional (only for simulation)

* Docker (https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-using-the-repository)

## Python dependencies
Python dependencies are listed in the requirements.txt of each subpackage. They can be installed
automatically by using `pip` by running the three commands below:

Run from the root of the repository:

* `pip install -r rbb_tools/requirements.txt`
* `pip install -r rbb_storage/requirements.txt`
* `pip install -r rbb_client/requirements.txt`

