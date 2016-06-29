import unittest
from mock import patch

import commands

import test_data


# test_command decorator
class test_command():

    def __init__(self, data=None):
        self.command = data.command
        self.mocked_input = data.mocked_input
        self.expected_response = data.expected_response
        self.admin = data.admin

        self.config = {
            "timesync_url": "test",
            "username": "test",
            "password": "test"
        }

    def authenticate_nonadmin(self):
        res = commands.sign_in(config_dict=self.config)

        return res

    def authenticate_admin(self):
        config_admin = dict(self.config)
        config_admin["username"] = "admin"

        res = commands.sign_in(config_dict=config_admin)

        return res

    def __call__(self, test):
        @patch("util.get_user_permissions")
        @patch("util.get_field")
        def test_wrapped(testcase, mock_get_field, mock_get_user_permissions):
            commands.connect(config_dict=self.config, test=True)

            # Set up mocks
            if "users" in self.expected_response:
                mock_get_user_permissions.return_value = \
                        self.expected_response["users"]

            mock_get_field.side_effect = self.mocked_input

            # Authenticate with TimeSync
            if self.admin:
                self.authenticate_admin()
            else:
                self.authenticate_nonadmin()

            # Run the command and perform the test
            response = self.command()

            test(testcase, self.expected_response, response)

        return test_wrapped


class CommandsTest(unittest.TestCase):

    @test_command(data=test_data.create_time_data)
    def test_create_time(self, expected, result):
        assert result == expected

    @test_command(data=test_data.update_time_data)
    def test_update_time(self, expected, result):
        assert result == expected

    @test_command(data=test_data.get_times_no_uuid_data)
    def test_get_times_no_uuid(self, expected, result):
        assert result == expected

    @test_command(data=test_data.get_times_uuid_data)
    def test_get_times_uuid(self, expected, result):
        assert result == expected

    @test_command(data=test_data.sum_times_data)
    def test_sum_times(self, expected, result):
        assert result == expected

    @test_command(data=test_data.delete_time_no_data)
    def test_delete_time_no(self, expected, result):
        assert result == expected

    @test_command(data=test_data.delete_time_data)
    def test_delete_time(self, expected, result):
        assert result == expected

    @test_command(data=test_data.create_project_data)
    def test_create_project(self, expected, result):
        assert result == expected

    @test_command(data=test_data.update_project_data)
    def test_update_project(self, expected, result):
        assert result == expected

    @test_command(data=test_data.get_projects_no_slug_data)
    def test_get_projects_no_slug(self, expected, result):
        assert result == expected

    @test_command(data=test_data.get_projects_slug_data)
    def test_get_projects_slug(self, expected, result):
        assert result == expected

    @test_command(data=test_data.delete_project_no_data)
    def test_delete_project_no(self, expected, result):
        assert result == expected

    @test_command(data=test_data.delete_project_data)
    def test_delete_project(self, expected, result):
        assert result == expected

    @test_command(data=test_data.create_activity_data)
    def test_create_activity(self, expected, result):
        assert result == expected

    @test_command(data=test_data.update_activity_data)
    def test_update_activity(self, expected, result):
        assert result == expected

    @test_command(data=test_data.get_activities_no_slug_data)
    def test_get_activities_no_slug(self, expected, result):
        assert result == expected

    @test_command(data=test_data.get_activities_slug_data)
    def test_get_activities_slug(self, expected, result):
        assert result == expected

    @test_command(data=test_data.delete_activity_no_data)
    def test_delete_activity_no(self, expected, result):
        assert result == expected

    @test_command(data=test_data.delete_activity_data)
    def test_delete_activity(self, expected, result):
        assert result == expected

    @test_command(data=test_data.create_user_data)
    def test_create_user(self, expected, result):
        assert result == expected

    @test_command(data=test_data.update_user_data)
    def test_update_user(self, expected, result):
        assert result == expected

    @test_command(data=test_data.get_users_no_slug_data)
    def test_get_users_no_slug(self, expected, result):
        assert result == expected

    @test_command(data=test_data.get_users_slug_data)
    def test_get_users_slug(self, expected, result):
        assert result == expected

    @test_command(data=test_data.delete_user_no_data)
    def test_delete_user_no(self, expected, result):
        assert result == expected

    @test_command(data=test_data.delete_user_data)
    def test_delete_user(self, expected, result):
        assert result == expected
