# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from rbb_swagger_server.models.bag_detailed import BagDetailed  # noqa: E501
from rbb_swagger_server.models.bag_extraction_configuration import BagExtractionConfiguration  # noqa: E501
from rbb_swagger_server.models.bag_store_detailed import BagStoreDetailed  # noqa: E501
from rbb_swagger_server.models.bag_summary import BagSummary  # noqa: E501
from rbb_swagger_server.models.binary import Binary  # noqa: E501
from rbb_swagger_server.models.comment import Comment  # noqa: E501
from rbb_swagger_server.models.error import Error  # noqa: E501
from rbb_swagger_server.models.file_detailed import FileDetailed  # noqa: E501
from rbb_swagger_server.models.file_store import FileStore  # noqa: E501
from rbb_swagger_server.models.session import Session  # noqa: E501
from rbb_swagger_server.models.simulation_detailed import SimulationDetailed  # noqa: E501
from rbb_swagger_server.models.simulation_environment_detailed import SimulationEnvironmentDetailed  # noqa: E501
from rbb_swagger_server.models.simulation_environment_summary import SimulationEnvironmentSummary  # noqa: E501
from rbb_swagger_server.models.simulation_run_detailed import SimulationRunDetailed  # noqa: E501
from rbb_swagger_server.models.simulation_run_summary import SimulationRunSummary  # noqa: E501
from rbb_swagger_server.models.simulation_summary import SimulationSummary  # noqa: E501
from rbb_swagger_server.models.tag import Tag  # noqa: E501
from rbb_swagger_server.models.task_detailed import TaskDetailed  # noqa: E501
from rbb_swagger_server.models.task_summary import TaskSummary  # noqa: E501
from rbb_swagger_server.models.user import User  # noqa: E501
from rbb_swagger_server.test import BaseTestCase


class TestBasicController(BaseTestCase):
    """BasicController integration test stubs"""

    def test_authorize_step_get(self):
        """Test case for authorize_step_get

        Authorization step forwarded to storage plugin
        """
        response = self.client.open(
            '/api/v0/file-storage/{store_name}/authorize/{step}'.format(store_name='store_name_example', step='step_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_authorize_step_post(self):
        """Test case for authorize_step_post

        Authorization step forwarded to storage plugin
        """
        response = self.client.open(
            '/api/v0/file-storage/{store_name}/authorize/{step}'.format(store_name='store_name_example', step='step_example'),
            method='POST')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_bag_store_authorize_step_get(self):
        """Test case for bag_store_authorize_step_get

        Authorization step forwarded to storage plugin
        """
        response = self.client.open(
            '/api/v0/stores/{store_name}/authorize/{step}'.format(store_name='store_name_example', step='step_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_bag_store_authorize_step_post(self):
        """Test case for bag_store_authorize_step_post

        Authorization step forwarded to storage plugin
        """
        response = self.client.open(
            '/api/v0/stores/{store_name}/authorize/{step}'.format(store_name='store_name_example', step='step_example'),
            method='POST')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_bag_comment(self):
        """Test case for delete_bag_comment

        Delete a comment
        """
        response = self.client.open(
            '/api/v0/stores/{store_name}/bags/{bag_name}/comments/{comment_id}'.format(store_name='store_name_example', bag_name='bag_name_example', comment_id=56),
            method='DELETE')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_extraction_configuration(self):
        """Test case for delete_extraction_configuration

        Delete extraction configuration
        """
        response = self.client.open(
            '/api/v0/extraction/configs/{config_name}'.format(config_name='config_name_example'),
            method='DELETE')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_file_store(self):
        """Test case for delete_file_store

        Delete file store
        """
        response = self.client.open(
            '/api/v0/file-storage/{store_name}'.format(store_name='store_name_example'),
            method='DELETE')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_session(self):
        """Test case for delete_session

        Delete a session or sessions
        """
        response = self.client.open(
            '/api/v0/sessions/{session_id}'.format(session_id='session_id_example'),
            method='DELETE')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_simulation(self):
        """Test case for delete_simulation

        Delete simulation
        """
        response = self.client.open(
            '/api/v0/simulations/{sim_identifier}'.format(sim_identifier=56),
            method='DELETE')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_simulation_environment(self):
        """Test case for delete_simulation_environment

        Delete simulation
        """
        response = self.client.open(
            '/api/v0/simulation-environments/{env_name}'.format(env_name='env_name_example'),
            method='DELETE')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_store(self):
        """Test case for delete_store

        Delete file store
        """
        response = self.client.open(
            '/api/v0/stores/{store_name}'.format(store_name='store_name_example'),
            method='DELETE')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_user_account(self):
        """Test case for delete_user_account

        Delete user account
        """
        response = self.client.open(
            '/api/v0/users/account/{alias}'.format(alias='alias_example'),
            method='DELETE')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_dequeue_task(self):
        """Test case for dequeue_task

        Take a task from the queue
        """
        query_string = [('worker_name', 'worker_name_example'),
                        ('tasks', 'tasks_example'),
                        ('labels', 'labels_example')]
        response = self.client.open(
            '/api/v0/queue/dequeue',
            method='POST',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_do_task_action(self):
        """Test case for do_task_action

        Perform an action on the task
        """
        task = TaskDetailed()
        query_string = [('action', 'action_example')]
        response = self.client.open(
            '/api/v0/queue/{task_identifier}'.format(task_identifier='task_identifier_example'),
            method='POST',
            data=json.dumps(task),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_bag_comments(self):
        """Test case for get_bag_comments

        List comments from bag
        """
        response = self.client.open(
            '/api/v0/stores/{store_name}/bags/{bag_name}/comments'.format(store_name='store_name_example', bag_name='bag_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_bag_file(self):
        """Test case for get_bag_file

        Get rosbag
        """
        response = self.client.open(
            '/api/v0/stores/{store_name}/bags/{bag_name}'.format(store_name='store_name_example', bag_name='bag_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_bag_meta(self):
        """Test case for get_bag_meta

        List products from bag
        """
        response = self.client.open(
            '/api/v0/stores/{store_name}/bags/{bag_name}/meta'.format(store_name='store_name_example', bag_name='bag_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_bag_tags(self):
        """Test case for get_bag_tags

        List tag from bag
        """
        response = self.client.open(
            '/api/v0/stores/{store_name}/bags/{bag_name}/tags'.format(store_name='store_name_example', bag_name='bag_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_current_user(self):
        """Test case for get_current_user

        Get current user information
        """
        response = self.client.open(
            '/api/v0/users/me',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_extraction_config(self):
        """Test case for get_extraction_config

        Get configuration details
        """
        response = self.client.open(
            '/api/v0/extraction/configs/{config_name}'.format(config_name='config_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_file(self):
        """Test case for get_file

        Get file
        """
        query_string = [('no_redirect', true)]
        response = self.client.open(
            '/api/v0/file-storage/{store_name}/{uid}/{file_name}'.format(store_name='store_name_example', uid=56, file_name='file_name_example'),
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_file_meta(self):
        """Test case for get_file_meta

        Get file meta data
        """
        response = self.client.open(
            '/api/v0/file-storage/{store_name}/{uid}/{file_name}/meta'.format(store_name='store_name_example', uid=56, file_name='file_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_file_store(self):
        """Test case for get_file_store

        Get store details
        """
        response = self.client.open(
            '/api/v0/file-storage/{store_name}'.format(store_name='store_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_simulation(self):
        """Test case for get_simulation

        Get simulation
        """
        query_string = [('expand', true)]
        response = self.client.open(
            '/api/v0/simulations/{sim_identifier}'.format(sim_identifier=56),
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_simulation_environment(self):
        """Test case for get_simulation_environment

        Get simulation environment
        """
        response = self.client.open(
            '/api/v0/simulation-environments/{env_name}'.format(env_name='env_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_simulation_run(self):
        """Test case for get_simulation_run

        Get simulation run
        """
        query_string = [('expand', true)]
        response = self.client.open(
            '/api/v0/simulations/{sim_identifier}/runs/{run_identifier}'.format(sim_identifier=56, run_identifier=56),
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_store(self):
        """Test case for get_store

        Get store details
        """
        response = self.client.open(
            '/api/v0/stores/{store_name}'.format(store_name='store_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_store_extraction_configs(self):
        """Test case for get_store_extraction_configs

        Get list of auto extraction configs
        """
        response = self.client.open(
            '/api/v0/stores/{store_name}/auto-extraction-configs'.format(store_name='store_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_tag(self):
        """Test case for get_tag

        Get tag info
        """
        response = self.client.open(
            '/api/v0/tags/{tag}'.format(tag='tag_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_task(self):
        """Test case for get_task

        Take a task from the queue
        """
        response = self.client.open(
            '/api/v0/queue/{task_identifier}'.format(task_identifier='task_identifier_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_user_account(self):
        """Test case for get_user_account

        Get user information
        """
        response = self.client.open(
            '/api/v0/users/account/{alias}'.format(alias='alias_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_bags(self):
        """Test case for list_bags

        List bags in store
        """
        query_string = [('limit', 56),
                        ('offset', 56),
                        ('ordering', 'ordering_example'),
                        ('discovered_gte', '2013-10-20T19:20:30+01:00'),
                        ('discovered_lte', '2013-10-20T19:20:30+01:00'),
                        ('start_time_gte', '2013-10-20T19:20:30+01:00'),
                        ('start_time_lte', '2013-10-20T19:20:30+01:00'),
                        ('end_time_gte', '2013-10-20T19:20:30+01:00'),
                        ('end_time_lte', '2013-10-20T19:20:30+01:00'),
                        ('duration_gte', 8.14),
                        ('duration_lte', 8.14),
                        ('meta_available', true),
                        ('is_extracted', true),
                        ('name', 'name_example'),
                        ('tags', 'tags_example'),
                        ('in_trash', true)]
        response = self.client.open(
            '/api/v0/stores/{store_name}/bags'.format(store_name='store_name_example'),
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_extraction_configurations(self):
        """Test case for list_extraction_configurations

        List available configurations
        """
        response = self.client.open(
            '/api/v0/extraction/configs',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_file_stores(self):
        """Test case for list_file_stores

        List available file stores
        """
        response = self.client.open(
            '/api/v0/file-storage',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_queue(self):
        """Test case for list_queue

        List task queue
        """
        query_string = [('limit', 56),
                        ('offset', 56),
                        ('ordering', 'ordering_example'),
                        ('running', 'running_example'),
                        ('finished', 'finished_example'),
                        ('queued', 'queued_example')]
        response = self.client.open(
            '/api/v0/queue',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_sessions(self):
        """Test case for list_sessions

        List current session
        """
        response = self.client.open(
            '/api/v0/sessions',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_simulation_environments(self):
        """Test case for list_simulation_environments

        List available simulation environments
        """
        response = self.client.open(
            '/api/v0/simulation-environments',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_simulation_runs(self):
        """Test case for list_simulation_runs

        List simulation runs
        """
        response = self.client.open(
            '/api/v0/simulations/{sim_identifier}/runs'.format(sim_identifier=56),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_simulations(self):
        """Test case for list_simulations

        List simulations
        """
        query_string = [('limit', 56),
                        ('offset', 56),
                        ('ordering', 'ordering_example')]
        response = self.client.open(
            '/api/v0/simulations',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_stores(self):
        """Test case for list_stores

        List available stores
        """
        response = self.client.open(
            '/api/v0/stores',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_tags(self):
        """Test case for list_tags

        List all tags
        """
        response = self.client.open(
            '/api/v0/tags',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_new_bag_comment(self):
        """Test case for new_bag_comment

        New bag comment
        """
        comment = Comment()
        response = self.client.open(
            '/api/v0/stores/{store_name}/bags/{bag_name}/comments'.format(store_name='store_name_example', bag_name='bag_name_example'),
            method='POST',
            data=json.dumps(comment),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_new_file(self):
        """Test case for new_file

        Register new file
        """
        file = FileDetailed()
        response = self.client.open(
            '/api/v0/file-storage/{store_name}'.format(store_name='store_name_example'),
            method='POST',
            data=json.dumps(file),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_new_session(self):
        """Test case for new_session

        Create a new session
        """
        response = self.client.open(
            '/api/v0/sessions',
            method='POST')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_new_simulation(self):
        """Test case for new_simulation

        New simulation
        """
        simulation = SimulationDetailed()
        query_string = [('trigger', 'trigger_example')]
        response = self.client.open(
            '/api/v0/simulations',
            method='POST',
            data=json.dumps(simulation),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_new_simulation_run(self):
        """Test case for new_simulation_run

        New simulation run
        """
        simulation_run = SimulationRunDetailed()
        response = self.client.open(
            '/api/v0/simulations/{sim_identifier}/runs'.format(sim_identifier=56),
            method='POST',
            data=json.dumps(simulation_run),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_new_task(self):
        """Test case for new_task

        Create a new task
        """
        task = TaskDetailed()
        response = self.client.open(
            '/api/v0/queue',
            method='POST',
            data=json.dumps(task),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_patch_bag_meta(self):
        """Test case for patch_bag_meta

        Partial update of bag information (this only supports a few fields)
        """
        bag = None
        query_string = [('trigger', 'trigger_example')]
        response = self.client.open(
            '/api/v0/stores/{store_name}/bags/{bag_name}/meta'.format(store_name='store_name_example', bag_name='bag_name_example'),
            method='PATCH',
            data=json.dumps(bag),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_put_bag_meta(self):
        """Test case for put_bag_meta

        Create/update bag information
        """
        bag = BagDetailed()
        query_string = [('trigger', 'trigger_example')]
        response = self.client.open(
            '/api/v0/stores/{store_name}/bags/{bag_name}/meta'.format(store_name='store_name_example', bag_name='bag_name_example'),
            method='PUT',
            data=json.dumps(bag),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_put_bag_tags(self):
        """Test case for put_bag_tags

        Change bag tags
        """
        tags = [List[str]()]
        query_string = [('auto_create', true)]
        response = self.client.open(
            '/api/v0/stores/{store_name}/bags/{bag_name}/tags'.format(store_name='store_name_example', bag_name='bag_name_example'),
            method='PUT',
            data=json.dumps(tags),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_put_current_user(self):
        """Test case for put_current_user

        Change current user information
        """
        user = User()
        response = self.client.open(
            '/api/v0/users/me',
            method='PUT',
            data=json.dumps(user),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_put_extraction_configuration(self):
        """Test case for put_extraction_configuration

        Create/update configuration
        """
        configuration_obj = BagExtractionConfiguration()
        response = self.client.open(
            '/api/v0/extraction/configs/{config_name}'.format(config_name='config_name_example'),
            method='PUT',
            data=json.dumps(configuration_obj),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_put_file_store(self):
        """Test case for put_file_store

        Create/update store
        """
        store = FileStore()
        response = self.client.open(
            '/api/v0/file-storage/{store_name}'.format(store_name='store_name_example'),
            method='PUT',
            data=json.dumps(store),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_put_simulation(self):
        """Test case for put_simulation

        Update a simulation
        """
        simulation = SimulationDetailed()
        response = self.client.open(
            '/api/v0/simulations/{sim_identifier}'.format(sim_identifier=56),
            method='PUT',
            data=json.dumps(simulation),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_put_simulation_environment(self):
        """Test case for put_simulation_environment

        Create/update a simulation environment
        """
        environment = SimulationEnvironmentDetailed()
        response = self.client.open(
            '/api/v0/simulation-environments/{env_name}'.format(env_name='env_name_example'),
            method='PUT',
            data=json.dumps(environment),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_put_store(self):
        """Test case for put_store

        Create/update store
        """
        store = BagStoreDetailed()
        response = self.client.open(
            '/api/v0/stores/{store_name}'.format(store_name='store_name_example'),
            method='PUT',
            data=json.dumps(store),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_put_store_extraction_configs(self):
        """Test case for put_store_extraction_configs

        Create/update store
        """
        store = [List[str]()]
        response = self.client.open(
            '/api/v0/stores/{store_name}/auto-extraction-configs'.format(store_name='store_name_example'),
            method='PUT',
            data=json.dumps(store),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_put_tag(self):
        """Test case for put_tag

        Create/update tag
        """
        tag_obj = Tag()
        response = self.client.open(
            '/api/v0/tags/{tag}'.format(tag='tag_example'),
            method='PUT',
            data=json.dumps(tag_obj),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_put_task(self):
        """Test case for put_task

        Update a task
        """
        task = TaskDetailed()
        response = self.client.open(
            '/api/v0/queue/{task_identifier}'.format(task_identifier='task_identifier_example'),
            method='PUT',
            data=json.dumps(task),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_put_user_account(self):
        """Test case for put_user_account

        Change user information
        """
        user = User()
        response = self.client.open(
            '/api/v0/users/account/{alias}'.format(alias='alias_example'),
            method='PUT',
            data=json.dumps(user),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
