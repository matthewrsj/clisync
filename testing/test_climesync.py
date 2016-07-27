import unittest
from mock import call, patch, MagicMock

from climesync import climesync
from climesync import commands


class ClimesyncTest(unittest.TestCase):

    @patch("climesync.commands.util")
    @patch("climesync.commands.pymesync.TimeSync")
    def test_connect_arg_url(self, mock_timesync, mock_util):
        baseurl = "ts_url"

        commands.connect(arg_url=baseurl)

        mock_util.add_kv_pair.assert_called_with("timesync_url", baseurl)
        mock_timesync.assert_called_with(baseurl=baseurl, test=False)

        commands.ts = None

    @patch("climesync.commands.util")
    @patch("climesync.commands.pymesync.TimeSync")
    def test_connect_config_dict(self, mock_timesync, mock_util):
        baseurl = "ts_url"
        config_dict = {"timesync_url": baseurl}

        commands.connect(config_dict=config_dict)

        mock_util.add_kv_pair.assert_called_with("timesync_url", baseurl)
        mock_timesync.assert_called_with(baseurl=baseurl, test=False)

        commands.ts = None

    @patch("climesync.commands.util")
    @patch("climesync.commands.pymesync.TimeSync")
    def test_connect_interactive(self, mock_timesync, mock_util):
        baseurl = "ts_url"

        mock_util.get_field.return_value = baseurl

        commands.connect()

        mock_util.add_kv_pair.assert_called_with("timesync_url", baseurl)
        mock_timesync.assert_called_with(baseurl=baseurl, test=False)

        commands.ts = None

    @patch("climesync.commands.util")
    @patch("climesync.commands.pymesync.TimeSync")
    def test_connect_noninteractive(self, mock_timesync, mock_util):
        baseurl = "ts_url"

        commands.connect(arg_url=baseurl, interactive=False)

        mock_util.add_kv_pair.assert_not_called()
        mock_timesync.assert_called_with(baseurl=baseurl, test=False)

        commands.ts = None

    def test_disconnect(self):
        commands.ts = MagicMock()

        commands.disconnect()

        assert not commands.ts

    @patch("climesync.commands.util")
    @patch("climesync.commands.ts")
    def test_sign_in_args(self, mock_ts, mock_util):
        username = "test"
        password = "password"

        mock_ts.test = False

        commands.sign_in(arg_user=username, arg_pass=password)

        mock_util.add_kv_pair.assert_has_calls([call("username", username),
                                                call("password", password)])
        mock_ts.authenticate.assert_called_with(username, password, "password")

    @patch("climesync.commands.util")
    @patch("climesync.commands.ts")
    def test_sign_in_config_dict(self, mock_ts, mock_util):
        username = "test"
        password = "password"
        config_dict = {"username": username, "password": password}

        mock_ts.test = False

        commands.sign_in(config_dict=config_dict)

        mock_util.add_kv_pair.assert_has_calls([call("username", username),
                                                call("password", password)])
        mock_ts.authenticate.assert_called_with(username, password, "password")

    @patch("climesync.commands.util")
    @patch("climesync.commands.ts")
    def test_sign_in_interactive(self, mock_ts, mock_util):
        username = "test"
        password = "test"
        mocked_input = [username, password]

        mock_util.get_field.side_effect = mocked_input

        mock_ts.test = False

        commands.sign_in()

        mock_util.add_kv_pair.assert_has_calls([call("username", username),
                                                call("password", password)])
        mock_ts.authenticate.assert_called_with(username, password, "password")

    @patch("climesync.commands.util")
    @patch("climesync.commands.ts")
    def test_sign_in_noninteractive(self, mock_ts, mock_util):
        username = "test"
        password = "test"

        mock_ts.test = False

        commands.sign_in(arg_user=username, arg_pass=password,
                         interactive=False)

        mock_util.add_kv_pair.assert_not_called()
        mock_ts.authenticate.assert_called_with(username, password, "password")

    def test_sign_in_not_connected(self):
        commands.ts = None

        response = commands.sign_in()

        assert "error" in response

    @patch("climesync.commands.ts")
    def test_sign_in_error(self, mock_ts):
        response = commands.sign_in(interactive=False)

        assert "climesync error" in response

    @patch("climesync.commands.ts")
    @patch("climesync.commands.pymesync.TimeSync")
    def test_sign_out(self, mock_timesync, mock_ts):
        url = "ts_url"
        test = False

        mock_ts.baseurl = url
        mock_ts.test = test

        commands.sign_out()

        mock_timesync.assert_called_with(baseurl=url, test=test)

    def test_sign_out_not_connected(self):
        commands.ts = None

        response = commands.sign_out()

        assert "error" in response

    @patch("climesync.climesync.commands")
    @patch("climesync.climesync.scripting_mode")
    def test_start_scripting(self, mock_scripting_mode, mock_commands):
        command = "create-time"
        argv = [command]

        climesync.main(argv=argv)

        mock_scripting_mode.assert_called_with("create-time", [])

    @patch("climesync.climesync.ClimesyncInterpreter")
    @patch("climesync.climesync.util")
    @patch("climesync.climesync.commands")
    def test_connect_args(self, mock_commands, mock_util, mock_interpreter):
        baseurl = "ts_url"
        username = "test"
        password = "password"
        argv = ["-c", baseurl, "-u", username, "-p", password]

        config_dict = {}

        mock_config = MagicMock()
        mock_config.items.return_value = config_dict

        mock_util.read_config.return_value = mock_config

        climesync.main(argv=argv, test=True)

        mock_commands.connect.assert_called_with(arg_url=baseurl,
                                                 config_dict=config_dict,
                                                 interactive=True,
                                                 test=True)
        mock_commands.sign_in.assert_called_with(arg_user=username,
                                                 arg_pass=password,
                                                 config_dict=config_dict,
                                                 interactive=True)

    @patch("climesync.climesync.scripting_mode")
    @patch("climesync.climesync.util.read_config")
    def test_main_use_config(self, mock_read_config, mock_scripting_mode):
        baseurl = "ts_url"
        username = "test"
        password = "password"
        argv = ["command"]

        config_dict = {
            "timesync_url": baseurl,
            "username": username,
            "password": password,
        }

        mock_config = MagicMock()
        mock_config.items.return_value = config_dict

        mock_read_config.return_value = mock_config

        climesync.main(argv=argv, test=True)

        mock_scripting_mode.assert_called_with("command", [])

    @patch("climesync.climesync.util")
    def test_main_connect_error(self, mock_util):
        username = "test"
        password = "test"
        argv = ["command"]

        config_dict = {"username": username, "password": password}

        mock_config = MagicMock()
        mock_config.items.return_value = config_dict

        mock_util.read_config.return_value = mock_config

        climesync.main(argv=argv, test=True)

        assert mock_util.print_json.call_count == 1

    @patch("climesync.climesync.util")
    def test_main_authenticate_error(self, mock_util):
        baseurl = "ts_url"
        argv = ["command"]

        config_dict = {"timesync_url": baseurl}

        mock_config = MagicMock()
        mock_config.items.return_value = config_dict

        mock_util.read_config.return_value = mock_config

        climesync.main(argv=argv, test=True)

        assert mock_util.print_json.call_count == 1
