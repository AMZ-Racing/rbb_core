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

INSERT INTO unittest.rbb_user ("uid", "alias", "full_name", "email", "password", "is_admin", "has_credential_access", "has_task_log_access") VALUES (DEFAULT, 'admin', 'Admin', 'admin@example.com', 'pbkdf2:sha256:50000$EYEeCBYq$571f59717fd2addb30ce609a78c9fdbd16482812a9d4956696919528132e1d98', true, true, true);
INSERT INTO unittest.rbb_user ("uid", "alias", "full_name", "email", "password", "is_admin", "has_credential_access") VALUES (DEFAULT, 'user', 'User', 'user@example.com', 'pbkdf2:sha256:50000$Rfbe2QUZ$993456f29968f83c834f6120041445c8b8e0824d8127e0fbc16436af67f0382c', false, false);

INSERT INTO unittest.file_store (uid, name, store_type, store_data, created) VALUES (DEFAULT, 'google-cloud', 'google-cloud', '{}', '2017-12-26 10:52:46.401969');
INSERT INTO unittest.file (uid, store_id, name, expires, store_data) VALUES (DEFAULT, 1, 'test.mp4', null, '{}');
INSERT INTO unittest.file_store (uid, name, store_type, store_data, created) VALUES (DEFAULT , 'test-file-store', 'rbb_storage_static', '{"static":{}}', '2017-12-26 10:52:46.401969');
INSERT INTO unittest.file_store (uid, name, store_type, store_data, created) VALUES (DEFAULT , 'delete-file-store', 'rbb_storage_static', '{"static":{}}', '2017-12-26 10:52:46.401969');

INSERT INTO unittest.file_store (uid, name, store_type, store_data, created) VALUES (DEFAULT, 's3-staging', 'rbb_storage_s3', '{
  "dummy": {} }', '2017-12-26 10:52:46.401969');

INSERT INTO unittest.rosbag_store (uid, name, description, created, store_type, store_data)
VALUES (DEFAULT , 'test-2', 'Mock storage plugin test', '2017-12-16 04:59:52.201754', 'rbb_storage_static', '{"static":{}}');

INSERT INTO unittest.rosbag_store (uid, name, description, created, store_type, store_data, default_file_store_id)
VALUES (DEFAULT , 'test', 'Mock storage plugin test', '2017-12-16 04:59:52.201754', 'rbb_storage_static', '{"static":{"test1.bag":{"link":"http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset/machine_hall/MH_01_easy/MH_01_easy.bag"}}}', 2);

INSERT INTO unittest.rosbag_store (uid, name, description, created, store_type, store_data, default_file_store_id)
VALUES (DEFAULT , 'test-3', 'Mock storage plugin test', '2017-12-16 04:59:52.201754', 'rbb_storage_static', '{"static":{},"indexable":false}', 1);

INSERT INTO unittest.rosbag (uid, store_id, extraction_failure, store_data, name, is_extracted, discovered, meta_available, size, start_time, end_time, duration, messages, comment)
VALUES (DEFAULT, 1, false, '{}', 'test-bag.bag', false, '2017-12-17 11:39:29.945440', false, 100, '2017-12-17 11:39:15.918000', '2017-12-17 11:39:18.133000', 10, 100, '');
INSERT INTO unittest.rosbag (uid, store_id, extraction_failure, store_data, name, is_extracted, discovered, meta_available, size, start_time, end_time, duration, messages, comment)
VALUES (DEFAULT, 1, false, '{}', 'empty.bag', false, '2017-12-17 11:39:29.945440', false, 0, '2017-12-17 11:39:15.918000', '2017-12-17 11:39:18.133000', 0, 0, '');

INSERT INTO unittest.rosbag_topic (uid, bag_id, name, msg_type, msg_type_hash, msg_definition, msg_count, avg_frequency) VALUES (DEFAULT, 1, '/camera1', 'Camera', '48utawojt9awu', 'empty', 1000, 50.4);
INSERT INTO unittest.rosbag_topic (uid, bag_id, name, msg_type, msg_type_hash, msg_definition, msg_count, avg_frequency) VALUES (DEFAULT, 1, '/camera2', 'Camera', 'ao84yytaiejfoij', 'empty', 2000, 100.2);

INSERT INTO unittest.rosbag_product (uid, bag_id, plugin, product_type, product_data, created) VALUES (DEFAULT , 1, 'RvizRecorder', 'movie', '{"type":"yolo"}', '2017-12-26 10:51:38.393607');
INSERT INTO unittest.rosbag_product (uid, bag_id, plugin, product_type, product_data, created) VALUES (DEFAULT , 1, 'RawVideo', 'movie', '{"type":"yolo"}', '2017-12-26 10:51:38.393607');
INSERT INTO unittest.rosbag_product (uid, bag_id, plugin, product_type, product_data, created) VALUES (DEFAULT , 1, 'RawVideo', 'rosbagstream', '{"type":"yolo"}', '2017-12-26 10:51:38.393607');

INSERT INTO unittest.rosbag_product_file (product_id, file_id, key) VALUES (1, 1, 'video');

INSERT INTO unittest.file (uid, store_id, name, expires, store_data) VALUES (DEFAULT, 1, 'video.mp4', null, '{}');


INSERT INTO unittest.rosbag (uid, store_id, extraction_failure, store_data, name, is_extracted, discovered, meta_available, size, start_time, end_time, duration, messages, comment)
VALUES (DEFAULT, 2, false, '{}', 'empty-mock-1.bag', false, '2017-12-17 11:39:29.945440', false, 0, '2017-12-17 11:39:15.918000', '2017-12-17 11:39:18.133000', 0, 0, '');
INSERT INTO unittest.rosbag (uid, store_id, extraction_failure, store_data, name, is_extracted, discovered, meta_available, size, start_time, end_time, duration, messages, comment)
VALUES (DEFAULT, 2, false, '{}', 'empty-mock-2.bag', false, '2018-1-17 11:39:29.945440', false, 0, '2017-12-17 11:39:15.918000', '2017-12-17 11:39:18.133000', 0, 0, '');
INSERT INTO unittest.rosbag (uid, store_id, extraction_failure, store_data, name, is_extracted, discovered, meta_available, size, start_time, end_time, duration, messages, comment)
VALUES (DEFAULT, 2, false, '{}', 'empty-mock-3.bag', false, '2018-2-17 11:39:29.945440', false, 0, '2017-12-17 11:39:15.918000', '2017-12-17 11:39:18.133000', 0, 0, '');
INSERT INTO unittest.rosbag (uid, store_id, extraction_failure, store_data, name, is_extracted, discovered, meta_available, size, start_time, end_time, duration, messages, comment)
VALUES (DEFAULT, 2, false, '{}', 'empty-mock-4.bag', false, '2018-3-17 11:39:29.945440', false, 0, '2017-12-17 11:39:15.918000', '2017-12-17 11:39:18.133000', 0, 0, '');
INSERT INTO unittest.rosbag (uid, store_id, extraction_failure, store_data, name, is_extracted, discovered, meta_available, size, start_time, end_time, duration, messages, comment)
VALUES (DEFAULT, 2, false, '{}', 'empty-mock-5.bag', false, '2018-4-20 11:39:29.945440', false, 0, '2017-12-17 11:39:15.918000', '2017-12-17 11:39:18.133000', 0, 0, '');
INSERT INTO unittest.rosbag (uid, store_id, extraction_failure, store_data, name, is_extracted, discovered, meta_available, size, start_time, end_time, duration, messages, comment)
VALUES (DEFAULT, 2, false, '{}', 'empty-mock-6.bag', false, '2018-4-28 11:39:29.945440', false, 0, '2017-12-17 11:39:15.918000', '2017-12-17 11:39:18.133000', 0, 0, '');
INSERT INTO unittest.rosbag (uid, store_id, extraction_failure, store_data, name, is_extracted, discovered, meta_available, size, start_time, end_time, duration, messages, comment)
VALUES (DEFAULT, 2, false, '{}', 'empty-mock-7.bag', false, '2018-4-26 11:39:29.945440', false, 0, '2017-12-17 11:39:15.918000', '2017-12-17 11:39:18.133000', 0, 0, '');
INSERT INTO unittest.rosbag (uid, store_id, extraction_failure, store_data, name, is_extracted, discovered, meta_available, size, start_time, end_time, duration, messages, comment)
VALUES (DEFAULT, 2, false, '{}', 'empty-mock-8.bag', false, '2017-12-17 11:39:29.945440', false, 0, '2017-12-17 11:39:15.918000', '2017-12-17 11:39:18.133000', 0, 0, '');
INSERT INTO unittest.rosbag (uid, store_id, extraction_failure, store_data, name, is_extracted, discovered, meta_available, size, start_time, end_time, duration, messages, comment)
VALUES (DEFAULT, 2, false, '{}', 'empty-mock-9.bag', false, '2017-12-17 11:39:29.945440', false, 0, '2017-12-17 11:39:15.918000', '2017-12-17 11:39:18.133000', 0, 0, '');
INSERT INTO unittest.rosbag (uid, store_id, extraction_failure, store_data, name, is_extracted, discovered, meta_available, size, start_time, end_time, duration, messages, comment)
VALUES (DEFAULT, 2, false, '{}', 'empty-mock-10.bag', false, '2017-12-17 11:39:29.945440', false, 0, '2017-12-17 11:39:15.918000', '2017-12-17 11:39:18.133000', 0, 0, '');
INSERT INTO unittest.rosbag (uid, store_id, extraction_failure, store_data, name, is_extracted, discovered, meta_available, size, start_time, end_time, duration, messages, comment)
VALUES (DEFAULT, 2, false, '{}', 'empty-mock-11.bag', false, '2017-12-17 11:39:29.945440', false, 0, '2017-12-17 11:39:15.918000', '2017-12-17 11:39:18.133000', 0, 0, '');
INSERT INTO unittest.rosbag (uid, store_id, extraction_failure, store_data, name, is_extracted, discovered, meta_available, size, start_time, end_time, duration, messages, comment, in_trash)
VALUES (DEFAULT, 1, false, '{}', 'trash.bag', false, '2017-12-17 11:39:29.945440', false, 0, '2017-12-17 11:39:15.918000', '2017-12-17 11:39:18.133000', 0, 0, '', true);

INSERT INTO unittest.rosbag_extraction_configuration ("uid", "name", "description", "config_type", "config")
VALUES (DEFAULT, 'test-config', 'Test configuration', 'git', '{"git":{"url":"https://github.com/hfchendrikx/rbb-visualizations.git","branch":"master","path":"rviz-test"}}');
INSERT INTO unittest.rosbag_extraction_association ("store_id", "config_id") VALUES (2, 1);
INSERT INTO unittest.rosbag_extraction_configuration ("uid", "name", "description", "config_type", "config")
VALUES (DEFAULT, 'test-config-2', 'Test configuration', 'git', '{"git":{"url":"https://github.com/hfchendrikx/rbb-visualizations.git","branch":"master","path":"rviz-test"}}');

INSERT INTO unittest.task_queue (uid, priority, description, assigned_to, created, state, task, configuration, result, success, runtime, log, worker_labels, task_hash) VALUES (DEFAULT, 1000, 'Success test', '', '2018-06-14 20:41:11.647354', 0, 'rbb_tools.tasks.test.success', '{}', '{}', false, 0, '', '', 'hash');
INSERT INTO unittest.task_queue (uid, priority, description, assigned_to, created, state, task, configuration, result, success, runtime, log, worker_labels, task_hash) VALUES (DEFAULT, 1000, 'Exception test', '', '2018-06-14 20:41:55.727840', 0, 'rbb_tools.tasks.test.causes_exception', '{}', '{}', false, 0, '', '', 'hash');
INSERT INTO unittest.task_queue (uid, priority, description, assigned_to, created, state, task, configuration, result, success, runtime, log, worker_labels, task_hash) VALUES (DEFAULT, 1001, 'Exit test', '', '2018-06-14 20:41:55.727840', 0, 'rbb_tools.tasks.test.exits', '{}', '{}', false, 0, '', '', 'hash');
INSERT INTO unittest.task_queue (uid, priority, description, assigned_to, created, state, task, configuration, result, success, runtime, log, worker_labels, task_hash) VALUES (DEFAULT, 1000, 'Waiting test', '', '2018-06-14 20:41:55.727840', 0, 'rbb_tools.tasks.test.waits', '{}', '{}', false, 0, '', '', 'hash');
INSERT INTO unittest.task_queue (uid, priority, description, assigned_to, created, state, task, configuration, result, success, runtime, log, worker_labels, task_hash) VALUES (DEFAULT, 1000, 'Extract x.bag', '', '2018-06-14 20:41:55.727840', 1, 'rbb_tools.tasks.test.success', '{}', '{}', false, 0, '', '', 'hash');
INSERT INTO unittest.task_queue (uid, priority, description, assigned_to, created, state, task, configuration, result, success, runtime, log, worker_labels, task_hash) VALUES (DEFAULT, 1000, 'Cancelled example', '', '2018-06-14 20:41:55.727840', 101, 'rbb_tools.tasks.test.success', '{}', '{}', false, 0, '', '', 'hash');
INSERT INTO unittest.task_queue (uid, priority, description, assigned_to, created, state, task, configuration, result, success, runtime, log, worker_labels, task_hash) VALUES (DEFAULT, 1000, 'Success exampe', '', '2018-06-14 20:41:55.727840', 100, 'rbb_tools.tasks.test.success', '{}', '{}', true, 5.239847, '', '', 'hash');
INSERT INTO unittest.task_queue (uid, priority, description, assigned_to, created, state, task, configuration, result, success, runtime, log, worker_labels, task_hash) VALUES (DEFAULT, 1000, 'Failure exampe', '', '2018-06-14 20:41:55.727840', 100, 'rbb_tools.tasks.test.success', '{}', '{}', false, 10.234234, '', '', 'hash');
INSERT INTO unittest.task_queue (uid, priority, description, assigned_to, created, state, task, configuration, result, success, runtime, log, worker_labels, task_hash) VALUES (DEFAULT, 1000, '10min streaming test', '', '2018-06-14 20:41:55.727840', 0, 'rbb_tools.tasks.test.long_task_streaming', '{}', '{}', false, 0, '', '', 'hash');

INSERT INTO unittest.tags (uid, tag, color) VALUES (DEFAULT , 'bad', '#C90707');
INSERT INTO unittest.tags (uid, tag, color) VALUES (DEFAULT , 'good', '#228B22');
INSERT INTO unittest.tags (uid, tag, color) VALUES (DEFAULT , 'super-bad', '#228B22');

INSERT INTO unittest.rosbag_tags (bag_id, tag_id) VALUES (1, 1);
INSERT INTO unittest.rosbag_tags (bag_id, tag_id) VALUES (2, 2);

INSERT INTO unittest.simulation_environment (uid, name, module, configuration, example_configuration, rosbag_store_id) VALUES (DEFAULT, 'test-sim-env', 'rbb_tools.simenvs.test', '{"test-env-config": "test"}', '// No configuration', null);
INSERT INTO unittest.simulation_environment (uid, name, module, configuration, example_configuration, rosbag_store_id) VALUES (DEFAULT, 'sim-env', 'rbb_tools.simenvs.scse', '{}', 'Balb abl', 1);

INSERT INTO unittest.simulation (uid, description, created, configuration, result, environment_id, task_in_queue_id, on_complete) VALUES (DEFAULT, 'Test simulation', '2018-06-21 09:00:46.930115', '{"test-sim-config": "test"}', 0, 1, 2, '{}');
INSERT INTO unittest.simulation (uid, description, created, configuration, result, environment_id, task_in_queue_id, on_complete) VALUES (DEFAULT, 'Test simulation', '2018-06-21 09:00:46.930115', '{}', 0, 1, 2, '{}');
INSERT INTO unittest.simulation (uid, description, created, configuration, result, environment_id, task_in_queue_id, on_complete) VALUES (DEFAULT, 'Test simulation', '2018-06-21 09:00:46.930115', '{}', 100, 1, null, '{}');
INSERT INTO unittest.simulation (uid, description, created, configuration, result, environment_id, task_in_queue_id, on_complete) VALUES (DEFAULT, 'Test simulation', '2018-06-21 09:00:46.930115', '{}', -100, 1, 2, '{}');
INSERT INTO unittest.simulation (uid, description, created, configuration, result, environment_id, task_in_queue_id, on_complete) VALUES (DEFAULT, 'Test delete simulation', '2018-06-21 09:00:46.930115', '{}', 0, 1, 2, '{}');

INSERT INTO unittest.simulation_run (uid, simulation_id, bag_id, description, success, duration, results) VALUES (DEFAULT, 1, 1, 'Loop', TRUE , 10, '{}');
INSERT INTO unittest.simulation_run (uid, simulation_id, bag_id, description, success, duration, results) VALUES (DEFAULT, 1, null, 'Eight', TRUE, 15.2, '{}');
INSERT INTO unittest.simulation_run (uid, simulation_id, bag_id, description, success, duration, results) VALUES (DEFAULT, 1, 1, 'Complicated', false, 1, '{}');
INSERT INTO unittest.simulation_run (uid, simulation_id, bag_id, description, success, duration, results) VALUES (DEFAULT, 1, 1, 'Accerlation', TRUE, 9, '{}');
INSERT INTO unittest.simulation_run (uid, simulation_id, bag_id, description, success, duration, results) VALUES (DEFAULT, 5, 1, 'Accerlation', TRUE, 9, '{}');

INSERT INTO unittest.rosbag_comment (bag_id, uid, user_id, comment_text, created) VALUES (2, DEFAULT, 1, 'Test comment', '2018-07-03 14:28:25.978520');
INSERT INTO unittest.rosbag_comment (bag_id, uid, user_id, comment_text, created) VALUES (2, DEFAULT, 1, 'Test comment 2', '2018-07-03 14:28:35.350022');