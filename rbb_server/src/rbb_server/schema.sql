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

-- USER & AUTHENTICATION

CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE "rbb_user" (
  uid SERIAL PRIMARY KEY,
  alias VARCHAR(50) NOT NULL UNIQUE,
  full_name VARCHAR(255) NOT NULL,
  email citext NOT NULL,
  password VARCHAR(255) NOT NULL,
  is_admin BOOLEAN DEFAULT FALSE,

  -- This is the temporary permission system
  has_credential_access BOOLEAN DEFAULT FALSE,
  has_task_log_access BOOLEAN DEFAULT FALSE
);

CREATE TABLE "token" (
  uid SERIAL PRIMARY KEY,
  "user_uid" INTEGER NOT NULL REFERENCES "rbb_user"(uid) ON DELETE CASCADE,
  token VARCHAR(255) NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  valid_for INTEGER DEFAULT 86400
);

CREATE TABLE "permission" (
  uid VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description VARCHAR(255) NOT NULL DEFAULT ''
);

INSERT INTO "permission" (uid, name, description) VALUES ('store_secret_access' , 'File/Bag Store Secrets Access', '');
INSERT INTO "permission" (uid, name, description) VALUES ('file_store_read' , 'File Stores Read', '');
INSERT INTO "permission" (uid, name, description) VALUES ('file_store_write' , 'File Stores Write', '');
INSERT INTO "permission" (uid, name, description) VALUES ('bag_store_read' , 'Bag Stores Read', '');
INSERT INTO "permission" (uid, name, description) VALUES ('bag_store_write' , 'Bag Stores Write', '');
INSERT INTO "permission" (uid, name, description) VALUES ('bag_read' , 'Bags Read', '');
INSERT INTO "permission" (uid, name, description) VALUES ('bag_write' , 'Bags Write', '');
INSERT INTO "permission" (uid, name, description) VALUES ('bag_comment_read' , 'Bag Comments Read', '');
INSERT INTO "permission" (uid, name, description) VALUES ('bag_comment_write' , 'Bag Comments Write', '');
INSERT INTO "permission" (uid, name, description) VALUES ('users_read' , 'Users Read', '');
INSERT INTO "permission" (uid, name, description) VALUES ('users_write' , 'Users Write', '');
INSERT INTO "permission" (uid, name, description) VALUES ('queue_read' , 'Queue Read', '');
INSERT INTO "permission" (uid, name, description) VALUES ('queue_write' , 'Queue Write', '');
INSERT INTO "permission" (uid, name, description) VALUES ('queue_result_access' , 'Queue Results Access', '');
INSERT INTO "permission" (uid, name, description) VALUES ('simenv_read' , 'Simulation Environments Read', '');
INSERT INTO "permission" (uid, name, description) VALUES ('simenv_write' , 'Simulation Environments Write', '');
INSERT INTO "permission" (uid, name, description) VALUES ('simenv_config_access' , 'Simulation Environments Configuration Access', '');
INSERT INTO "permission" (uid, name, description) VALUES ('sim_read' , 'Simulations Read', '');
INSERT INTO "permission" (uid, name, description) VALUES ('sim_write' , 'Simulations Write', '');
INSERT INTO "permission" (uid, name, description) VALUES ('config_read' , 'System Configuration Read', '');
INSERT INTO "permission" (uid, name, description) VALUES ('config_write' , 'System Configuration Write', '');
INSERT INTO "permission" (uid, name, description) VALUES ('config_secret_access' , 'System Configuration Secrets Access', '');

CREATE TABLE "user_permissions" (
  user_id INTEGER NOT NULL REFERENCES rbb_user(uid) ON DELETE CASCADE,
  permission_id VARCHAR(50) NOT NULL REFERENCES permission(uid) ON DELETE CASCADE,
  PRIMARY KEY (user_id, permission_id)
);

-- CONFIG KEY VALUE

CREATE TABLE "configuration" (
  config_key VARCHAR(255) PRIMARY KEY,
  value TEXT NOT NULL,
  description VARCHAR(255) NOT NULL DEFAULT ''
);

INSERT INTO "configuration" (config_key, value, description) VALUES ('secret.jenkins.user' , '', '');
INSERT INTO "configuration" (config_key, value, description) VALUES ('secret.jenkins.password' , '', '');
INSERT INTO "configuration" (config_key, value, description) VALUES ('worker.default.poll_interval' , '10', '');
INSERT INTO "configuration" (config_key, value, description) VALUES ('worker.default.update_interval' , '20', '');

-- BAG MANAGEMENT

CREATE TABLE "tags" (
  uid SERIAL PRIMARY KEY,
  tag VARCHAR(100) NOT NULL UNIQUE,
  color VARCHAR(10)
);

CREATE TABLE "file_store" (
  uid SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  store_type VARCHAR(50) NOT NULL,
  store_data json NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);

CREATE TABLE "rosbag_store" (
  uid SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  description text NOT NULL,
  store_type VARCHAR(50) NOT NULL,
  store_data json NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  default_file_store_id INTEGER REFERENCES file_store(uid) ON DELETE SET NULL
);

CREATE TABLE "rosbag" (
  -- Basics
  uid SERIAL PRIMARY KEY,
  store_id INTEGER NOT NULL REFERENCES rosbag_store(uid) ON DELETE CASCADE,
  store_data json NOT NULL,
  name VARCHAR(255) NOT NULL,
  is_extracted BOOLEAN NOT NULL DEFAULT FALSE,
  in_trash BOOLEAN NOT NULL DEFAULT FALSE,
  extraction_failure BOOLEAN NOT NULL DEFAULT FALSE,
  discovered TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  UNIQUE (store_id, name),

  -- Meta
  meta_available BOOLEAN NOT NULL DEFAULT FALSE,
  size BIGINT,
  start_time timestamp,
  end_time timestamp,
  duration DOUBLE PRECISION,
  messages BIGINT,

  -- Additional
  comment text NOT NULL
);

CREATE TABLE "rosbag_tags" (
  bag_id INTEGER NOT NULL REFERENCES rosbag(uid) ON DELETE CASCADE,
  tag_id INTEGER NOT NULL REFERENCES tags(uid) ON DELETE CASCADE,
  PRIMARY KEY (bag_id, tag_id)
);

CREATE TABLE "rosbag_topic" (
  uid SERIAL PRIMARY KEY,
  bag_id INTEGER NOT NULL REFERENCES rosbag(uid) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  msg_type VARCHAR(255) NOT NULL,
  msg_type_hash VARCHAR(50) NOT NULL,
  msg_definition text NOT NULL,
  msg_count INTEGER NOT NULL,
  avg_frequency FLOAT NOT NULL,
  UNIQUE (bag_id, name)
);

CREATE TABLE "rosbag_product" (
  uid SERIAL PRIMARY KEY,
  bag_id INTEGER NOT NULL REFERENCES rosbag(uid) ON DELETE CASCADE,
  plugin VARCHAR(100) NOT NULL,
  product_type VARCHAR(100) NOT NULL,
  product_data json NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  title VARCHAR(200) NOT NULL DEFAULT '',
  configuration_tag VARCHAR(100) NOT NULL DEFAULT '',
  configuration_rule VARCHAR(100) NOT NULL DEFAULT ''
);

CREATE TABLE "rosbag_product_topic" (
  product_id INTEGER NOT NULL REFERENCES rosbag_product(uid) ON DELETE CASCADE,
  topic_id INTEGER NOT NULL REFERENCES rosbag_topic(uid) ON DELETE CASCADE,
  plugin_topic VARCHAR(255) NOT NULL,
  PRIMARY KEY (product_id, topic_id)
);

CREATE TABLE "rosbag_extraction_configuration" (
  uid SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description VARCHAR(255) NOT NULL,
  config_type VARCHAR(255) NOT NULL,
  config json NOT NULL,
  UNIQUE(name)
);

CREATE TABLE "rosbag_extraction_association" (
  store_id INTEGER NOT NULL REFERENCES rosbag_store(uid) ON DELETE CASCADE,
  config_id INTEGER NOT NULL REFERENCES rosbag_extraction_configuration(uid) ON DELETE CASCADE,
  PRIMARY KEY (store_id, config_id)
);

-- STORAGE (sim bags & extraction data)

CREATE TABLE "file" (
  uid SERIAL PRIMARY KEY,
  store_id INTEGER NOT NULL REFERENCES file_store(uid) ON DELETE RESTRICT,
  name VARCHAR(255) NOT NULL,
  expires TIMESTAMP,
  store_data json NOT NULL
);

CREATE TABLE "rosbag_product_file" (
  product_id INTEGER NOT NULL REFERENCES rosbag_product(uid) on DELETE CASCADE,
  file_id INTEGER NOT NULL REFERENCES file(uid) on DELETE CASCADE,
  key VARCHAR(50) NOT NULL,
  PRIMARY KEY (product_id, file_id)
);

-- JOB QUEUE

CREATE TABLE "task_queue" (
  uid SERIAL PRIMARY KEY,
  priority INTEGER NOT NULL DEFAULT 0,
  description VARCHAR(200),
  assigned_to VARCHAR(100),
  created TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  last_updated TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  state SMALLINT NOT NULL DEFAULT 0,
  task VARCHAR(100) NOT NULL,
  configuration json NOT NULL,
  result json NOT NULL,
  success BOOLEAN,
  runtime FLOAT,
  log TEXT,
  worker_labels VARCHAR(255),
  task_hash VARCHAR(50)
);

CREATE INDEX ON task_queue (task, task_hash);

-- SIMULATION

CREATE TABLE "simulation_environment" (
  uid SERIAL PRIMARY KEY,
  name VARCHAR(200) NOT NULL UNIQUE,
  module VARCHAR(200) NOT NULL,
  configuration json NOT NULL,
  example_configuration TEXT NOT NULL,
  rosbag_store_id INTEGER NULL REFERENCES rosbag_store(uid) on DELETE SET NULL
);

CREATE TABLE "simulation" (
  uid SERIAL PRIMARY KEY,
  description VARCHAR(250) NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
  configuration json NOT NULL,
  result SMALLINT NOT NULL DEFAULT 0,
  environment_id INTEGER NOT NULL REFERENCES simulation_environment(uid) on DELETE CASCADE,
  task_in_queue_id INTEGER NULL REFERENCES task_queue(uid) on DELETE SET NULL,
  on_complete json NULL
);

CREATE TABLE "simulation_run" (
  uid SERIAL PRIMARY KEY,
  simulation_id INTEGER NOT NULL REFERENCES simulation(uid) on DELETE CASCADE,
  bag_id INTEGER NULL REFERENCES rosbag(uid) on DELETE SET NULL,
  description VARCHAR(200) NOT NULL,
  success BOOLEAN NOT NULL,
  duration FLOAT NOT NULL,
  results json NOT NULL
);

-- COMMENTING

CREATE TABLE "rosbag_comment" (
  bag_id INTEGER NOT NULL REFERENCES rosbag(uid) ON DELETE CASCADE,

  uid SERIAL PRIMARY KEY,
  user_id INTEGER NULL REFERENCES rbb_user(uid) on DELETE SET NULL,
  comment_text VARCHAR(1000),
  created TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);
