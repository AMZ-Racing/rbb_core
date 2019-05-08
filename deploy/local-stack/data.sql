-- AMZ-Driverless
-- Copyright (c) 2019 Authors:
--   - Huub Hendrikx <hhendrik@ethz.ch>
--
-- Permission is hereby granted, free of charge, to any person obtaining a copy
-- of this software and associated documentation files (the "Software"), to deal
-- in the Software without restriction, including without limitation the rights
-- to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
-- copies of the Software, and to permit persons to whom the Software is
-- furnished to do so, subject to the following conditions:
--
-- The above copyright notice and this permission notice shall be included in all
-- copies or substantial portions of the Software.
--
-- THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
-- IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
-- FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
-- AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
-- LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
-- OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
-- SOFTWARE.

INSERT INTO rbb_user ("uid", "alias", "full_name", "email", "password", "is_admin", "has_credential_access", "has_task_log_access")
  VALUES (DEFAULT, 'admin', 'Admin', 'admin@test.com',
          'pbkdf2:sha256:50000$hEU12t9Y$7437dbd66b1eca2591dc21339fce9f61624dcd4cb2a6f25e19458fce1c25f2cd', true, true, true);

INSERT INTO file_store ("uid", "name", "store_type", "store_data", "created") VALUES (DEFAULT, 'generated', 'rbb_storage_s3', '{
  "s3": {
    "endpoint-url":"http://minio.rbb.localhost:9000",
    "aws-access-key-id":"MINIOKEY",
    "aws-secret-access-key":"MINIOSUPERSECRET",
    "bucket": "media",
    "key_prefix": "data/",
    "indexable": true,
    "signed_links": true
  }
}', '2018-11-15 16:08:34.846545');

-- For minio signed links are necessary, because unsigned links are a S3 hack
INSERT INTO rosbag_store ("uid", "name", "description", "store_type", "store_data", "created", "default_file_store_id") VALUES (DEFAULT, 'local-stack-minio', 'Bags stored in bags bucket of the minio container', 'rbb_storage_s3', '{
  "s3": {
    "endpoint-url":"http://minio.rbb.localhost:9000",
    "aws-access-key-id":"MINIOKEY",
    "aws-secret-access-key":"MINIOSUPERSECRET",
    "bucket": "bags",
    "key_prefix": "data/bags/",
    "indexable": true,
    "signed_links": true
  }
}', '2018-11-15 15:54:12.002870', 1);

INSERT INTO rosbag_store ("uid", "name", "description", "store_type", "store_data", "created", "default_file_store_id") VALUES (DEFAULT, 'local-stack-minio-sim', 'Bags recorded from simulation', 'rbb_storage_s3', '{
  "s3": {
    "endpoint-url":"http://minio.rbb.localhost:9000",
    "aws-access-key-id":"MINIOKEY",
    "aws-secret-access-key":"MINIOSUPERSECRET",
    "bucket": "bags",
    "key_prefix": "data/simulation/",
    "indexable": true,
    "signed_links": true
  }
}', '2018-11-15 15:54:12.002870', 1);

INSERT INTO rosbag_store ("uid", "name", "description", "store_type", "store_data", "created", "default_file_store_id") VALUES (DEFAULT, 'third-party-bags', 'External interesting bags', 'rbb_storage_static', '{
  "static": {
    "EuRoC_MH_04_difficult.bag": {"link": "http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset/machine_hall/MH_04_difficult/MH_04_difficult.bag"},
    "EuRoC_V2_03_difficult.bag": {"link": "http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset/vicon_room2/V2_03_difficult/V2_03_difficult.bag"},
    "amz-2017-05-10-13-14-16.bag": {"link": "https://www.dropbox.com/s/74ghqky8exj2820/2017-05-10-13-14-16.public-release.bag?dl=1"}
    }
}', '2018-11-15 15:54:12.002870', 1);

INSERT INTO rosbag_extraction_configuration ("uid", "name", "description", "config_type", "config") VALUES (DEFAULT, 'rbb-visualizations-cameras', 'Camera Video Test', 'git', '{"git":{"url":"https://github.com/hfchendrikx/rbb-visualizations.git","branch":"master","path":"camera-test"}}');
INSERT INTO rosbag_extraction_configuration ("uid", "name", "description", "config_type", "config") VALUES (DEFAULT, 'rbb-visualizations-rviz', 'RViz Test', 'git', '{"git":{"url":"https://github.com/hfchendrikx/rbb-visualizations.git","branch":"master","path":"rviz-test"}}');
INSERT INTO rosbag_extraction_configuration ("uid", "name", "description", "config_type", "config") VALUES (DEFAULT, 'rbb-visualizations-sim', 'Simulation Test', 'git', '{"git":{"url":"https://github.com/hfchendrikx/rbb-visualizations.git","branch":"master","path":"simulation-test"}}');
INSERT INTO rosbag_extraction_configuration ("uid", "name", "description", "config_type", "config") VALUES (DEFAULT, 'rbb-visualizations-topic-info', 'Topic Info', 'git', '{"git":{"url":"https://github.com/hfchendrikx/rbb-visualizations.git","branch":"master","path":"topic-info"}}');
INSERT INTO rosbag_extraction_configuration ("uid", "name", "description", "config_type", "config") VALUES (DEFAULT, 'rbb-visualizations-euroc', 'EuRoC example', 'git', '{"git":{"url":"https://github.com/hfchendrikx/rbb-visualizations.git","branch":"master","path":"euroc"}}');
INSERT INTO rosbag_extraction_configuration ("uid", "name", "description", "config_type", "config") VALUES (DEFAULT, 'rbb-visualizations-fssim', 'FSSIM Demo', 'git', '{"git":{"url":"https://github.com/hfchendrikx/rbb-visualizations.git","branch":"master","path":"fssim-demo"}}');

INSERT INTO rosbag_extraction_association ("store_id", "config_id") VALUES (1, 1);

INSERT INTO rosbag_extraction_association ("store_id", "config_id") VALUES (2, 3);
INSERT INTO rosbag_extraction_association ("store_id", "config_id") VALUES (2, 4);
INSERT INTO rosbag_extraction_association ("store_id", "config_id") VALUES (2, 6);

INSERT INTO rosbag_extraction_association ("store_id", "config_id") VALUES (3, 1);
INSERT INTO rosbag_extraction_association ("store_id", "config_id") VALUES (3, 4);
INSERT INTO rosbag_extraction_association ("store_id", "config_id") VALUES (3, 5);

INSERT INTO simulation_environment ("uid", "name", "module", "configuration", "example_configuration", "rosbag_store_id") VALUES
  (DEFAULT, 'rbb-sample-simulation', 'rbb_tools.simenvs.scse', '{
  "image": "ros:kinetic-robot-xenial",
  "workspace": "/ws",
  "setup_script": "#!/bin/bash\nsource /opt/ros/kinetic/setup.bash\nprintenv\nsudo apt-get update\nsudo apt-get install -y ssh-client software-properties-common python-catkin-tools build-essential sudo python-pip\nmkdir ~/.ssh\nssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts\ngit clone -b \"$GIT_BRANCH\" --single-branch https://github.com/hfchendrikx/rbb-sample-simulation.git\ncd rbb-sample-simulation\npip install subprocess32\ncatkin --no-color build --no-status",
  "env_vars": {
    "fixed": {"FIXED_ENV": "This should not be changeable"},
    "overridable": {"GIT_BRANCH": "master"}
  },
  "host_ssh_agent": true,
  "simulator_script": "#!/bin/bash\nsource ./rbb-sample-simulation/devel/setup.bash\n./rbb-sample-simulation/src/outputs_a_sine/test_record.py ${SIMULATOR_CONFIG}"
}', 'env_vars:
  # This branch is checked out for testing
  GIT_BRANCH: "master"
# This is written to config.yaml and passed to the simulator script
simulator_config:
  some-key: test
', 2);

INSERT INTO simulation_environment ("uid", "name", "module", "configuration", "example_configuration", "rosbag_store_id") VALUES
  (DEFAULT, 'fssim-simulation', 'rbb_tools.simenvs.scse', '{
  "env_vars": {
    "fixed": {
      "FIXED_ENV": "This should not be changeable"
    },
    "overridable": {
      "GIT_BRANCH": "master"
    }
  },
  "host_ssh_agent": true,
  "image": "ros:kinetic-robot-xenial",
  "setup_script": "#!/bin/bash\nsource /opt/ros/kinetic/setup.bash\n# Update and install software\nsudo apt-get update\nsudo apt-get install -y ssh-client software-properties-common python-catkin-tools build-essential sudo python-pip checkinstall libyaml-cpp-dev\npip install subprocess32\n# Trust github.com\nmkdir ~/.ssh\nssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts\n# Setup catkin workspace\nmkdir -p ws/src\ncd ws\ncatkin init\ncd src\ngit clone -b \"$GIT_BRANCH\" --single-branch https://github.com/AMZ-Driverless/fsd_skeleton.git\n# Install dependencies\ncd fsd_skeleton\n./update_dependencies.sh -f\n# Build\ncatkin --no-color build --no-status",
  "simulator_script": "#!/bin/bash\nsource ./ws/devel/setup.bash\n./ws/src/fsd_skeleton/src/fssim/fssim/scripts/launch.py --config ./ws/src/fsd_skeleton/src/fssim_interface/fssim_config/ats_simulation.yaml --output ${SIMULATOR_OUTPUT}",
  "workspace": "/ws"
}', 'env_vars:
  # This branch is checked out for testing
  GIT_BRANCH: "master"
# This is written to config.yaml and passed to the simulator script
simulator_config:
  some-key: test
', 2);
