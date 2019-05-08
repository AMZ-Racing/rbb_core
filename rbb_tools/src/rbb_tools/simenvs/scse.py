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

import getpass
import logging
import os
import sys

import docker
import docker.types
import yaml

from rbb_tools.simenvs.environment import SimulationEnvironment


class SCSESimulationEnvironment(SimulationEnvironment):

    def __init__(self, env_config, sim_config, output_dir, tmp_dir):
        super(SCSESimulationEnvironment, self).__init__(env_config, sim_config, output_dir, tmp_dir)

        self._shared_dir_path = self._tmp_dir + "/shared"
        self._workspace_host_path = self._tmp_dir + "/workspace"

        self._container_image = env_config['image']
        self._workspace = env_config['workspace']
        self._clean_workspace = env_config['clean_workspace'] if 'clean_workspace' in env_config else False
        self._host_ssh_agent = env_config['host_ssh_agent']
        self._setup_script = env_config['setup_script']
        self._simulator_script = env_config['simulator_script']
        self._simulator_config = sim_config['simulator_config']
        self._setup_env(env_config['env_vars']['fixed'], env_config['env_vars']['overridable'], sim_config['env_vars'])

        # Get user information to run as the current user inside docker
        # this solves the file permissions problem
        self._user_uid = os.getuid()
        self._user_guid = os.getgid()
        self._user_name = getpass.getuser()

        # Scripts can block for max 15 minutes, git clone can take long time
        self._dc = docker.from_env(timeout=900)
        self._container = None

    def _setup_env(self, fixed_env, overridable_env, sim_env):
        self._env = {
            'WORKSPACE': self._workspace,
            'SIMULATOR_CONFIG': "/ats_shared/config.yaml",
            'SIMULATOR_OUTPUT': "/ats_output"
        }

        if isinstance(fixed_env, dict):
            for var in fixed_env:
                self._env[var] = fixed_env[var]

        if isinstance(overridable_env, dict):
            if isinstance(sim_env, dict):
                for var in sim_env:
                    if var in overridable_env:
                        overridable_env[var] = sim_env[var]

            for var in overridable_env:
                value = overridable_env[var]
                if value is not None:
                    self._env[var] = value

        if self._host_ssh_agent:
            self._env['SSH_AUTH_SOCK'] = os.environ.get("SSH_AUTH_SOCK")

    def _exec_to_stdout(self, cmd, as_root=False):
        if as_root:
            resp = self._dc.api.exec_create(self._container.id, cmd,
                                            environment=self._env,
                                            workdir=self._workspace)
        else:
            resp = self._dc.api.exec_create(self._container.id, cmd,
                                            environment=self._env,
                                            workdir=self._workspace,
                                            user=self._user_name)

        exec_output = self._dc.api.exec_start(
            resp['Id'], stream=True
        )

        for output in exec_output:
            sys.stdout.write(output)

        code = self._dc.api.exec_inspect(resp['Id'])['ExitCode']
        return code

    def _create_shared_file(self, name, contents, chmod=0o444):
        with open(self._shared_dir_path + "/" + name, 'w') as f:
            f.write(contents)
        os.chmod(self._shared_dir_path + "/" + name, chmod)

    def prepare(self):
        # Created directory shared with container
        if not os.path.exists(self._shared_dir_path):
            os.makedirs(self._shared_dir_path)

        # Create workspace directory for the setup script
        if not os.path.exists(self._workspace_host_path):
            os.makedirs(self._workspace_host_path)

        clean_script = "#!/bin/bash \n" \
                       "echo \"Cleaning ${WORKSPACE}\"\n" \
                       "sudo rm -rf \"${WORKSPACE}/\"*"
        self._create_shared_file("clean", clean_script, 0o777)

        uid = str(self._user_uid)
        guid = str(self._user_guid)

        # Recreate the current user inside the docker container and allow it to use sudo
        sudo_script = "#!/bin/bash \n" \
                      "apt-get update && apt-get install sudo -y\n" \
                      "groupadd -g "+guid+" "+self._user_name+" \n" \
                      "useradd -m -u "+uid+" -g "+guid+" -s /bin/bash "+self._user_name+"\n" \
                      "echo \"\n"+self._user_name+" ALL=(ALL) NOPASSWD:ALL\" > /etc/sudoers"

        # Used to transfer the files to the current user, should not be needed anymore now we run as the current user
        transfer_ownership_script = "#!/bin/bash \n" \
                                    "chown -R "+uid+":"+guid+" \"${WORKSPACE}/\"* \n" \
                                    "chown -R "+uid+":"+guid+" \"${SIMULATOR_OUTPUT}/\"* \n"

        self._create_shared_file("enable_sudo", sudo_script, 0o777)
        self._create_shared_file("clean", clean_script, 0o777)
        self._create_shared_file("setup", self._setup_script, 0o777)
        self._create_shared_file("simulate", self._simulator_script, 0o777)
        self._create_shared_file("transfer_ownership", transfer_ownership_script, 0o777)

        with open(self._shared_dir_path + "/config.yaml", 'w') as f:
            yaml.safe_dump(self._simulator_config, f, default_flow_style=False)
        os.chmod(self._shared_dir_path + "/config.yaml", 0o744)

        # Connection to the outside world
        volumes = {
            self._shared_dir_path: {'bind': '/ats_shared', 'mode': 'ro'},
            self._workspace_host_path: {'bind': self._workspace, 'mode': 'rw'},
            self._output_dir: {'bind': '/ats_output', 'mode': 'rw'}
        }

        if self._host_ssh_agent:
            host_sock = os.environ.get("SSH_AUTH_SOCK")
            if host_sock:
                volumes[host_sock] = {'bind': host_sock, 'mode': 'rw'}
            else:
                logging.warning("Cannot mount ssh agent, SSH_AUTH_SOCK is not available")

        # Start container
        self._container = self._dc.containers.run(self._container_image, 'tail -f /dev/null',
                                                  auto_remove=True,
                                                  detach=True,
                                                  volumes=volumes)

        # Add the current user and enable sudo
        self._exec_to_stdout("/ats_shared/enable_sudo", as_root=True)

        # Run clean
        if self._clean_workspace:
            self._exec_to_stdout("/ats_shared/clean")

        # Run setup
        code = self._exec_to_stdout("/ats_shared/setup")

        if code != 0:
            return False

        return True

    def simulate(self):
        # Run simulation
        code = self._exec_to_stdout("/ats_shared/simulate")

        if code != 0:
            return False

        return True

    def clean(self):
        # Files created from inside the docker container are owned by root
        # The transfer_ownership script will change the owner to current user
        if self._container:
            # logging.info("Transferring file ownership...")
            # #self._container.exec_run("/ats_shared/transfer_ownership")
            # logging.info("Transferring file ownership is disabled, needs investigation!")

            logging.info("Removing container...")
            self._container.remove(force=True)


environment = SCSESimulationEnvironment

