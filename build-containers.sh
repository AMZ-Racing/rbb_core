#!/bin/sh

echo "BUILDING API SERVER CONTAINER..."
docker build -t amzracing/rbb-api-server:latest -f deploy/api-server.docker .

echo "\n\nBUILDING KINETIC NO-GPU WORKER CONTAINER..."
docker build -t amzracing/rbb-tools:kinetic -f deploy/worker-kinetic-no-gpu.docker .

echo "\n\nBUILDING NVIDIA|OPENGL|ROS CONTAINER..."
docker build -t ros-kinetic-desktop-nvidia-opengl:latest -f deploy/docker-ros-kinetic-desktop-nvidia.docker .
echo "\n\nBUILDING GPU WORKER CONTAINER..."
docker build -t amzracing/rbb-tools-gpu-nvidia:latest -f deploy/worker-kinetic-gpu.docker .
