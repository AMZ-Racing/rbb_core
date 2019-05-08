# Running a worker node (on AWS)

**NOTE** The Rviz recorder might need a GPU machine for hardware rendering.

### Getting GPU machine ready on AWS

Only follow this when you want to use RViz on an AWS machine.

1. Follow AWS installation guidelines (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/install-nvidia-driver.html). Ubuntu 16.04 works with 	367.124.
3. Intall xorg `install xserver-xorg-core`
2. Add the configuration for nvidia `nvidia-xconfig -a --use-display-device=None --virtual=1920x1200`
3. You might need to copy the generated xserver config to the xserver configuration directory (e.g. /usr/share/X11/xorg.conf.d). It might also be necessary to add the BusID of the card to the config and a module path to find the nvidia driver (nvidia_drv.so).
4. Run an X Server with `sudo X :0`
5. Make sure that the terminal that will run the worker has the display set in the environment `export DISPLAY=:0`

### Installing dependencies

1. Install the dependencies listed above.
2. Install docker (https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-using-the-repository)
3. Install ROS (kinetic-desktop)
4. Install the python requirements for rbb_tools `pip install -r rbb_tools/requirements.txt`, `pip install -r rbb_client/requirements.txt`, `pip install -r rbb_storage/requirements.txt`
5. In case you run on a server you might need to run an `ssh-agent` with keys needed for the simulation repositories

### For running FSSIM simulations

1. Somewhere on you computer clone autonomous_2018, and clone fssim inside the autonomous_2018 workspace.
2. Run the docker container build script `src/continuous_integration/build-gotthard-containers -f`

### Running the node

1. Authorize the current user `rbbtools -u USERNAME -p PASSWORD authorize`
2. Run the command `rbbtools work`
