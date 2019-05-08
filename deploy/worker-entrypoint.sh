#!/usr/bin/env bash

# The ros environment scripts somehow crash with arguments set
ARGS="$@"
set -- ""
source /opt/ros/kinetic/setup.bash

/var/app/rbb_tools/rbbtools $ARGS
