from datetime import date

import pymesync
from docopt import docopt

import util

ts = None  # pymesync.TimeSync object


# climesync_command decorator
class climesync_command():

    def __init__(self, select_arg=None, optional_args=False):
        self.select_arg = select_arg
        self.optional_args = optional_args

    def __call__(self, command):
        def wrapped_command(argv=None):
            if argv is not None:
                args = docopt(command.__doc__, argv=argv)

                command_kwargs = {}

                # Put values gotten from docopt into a Pymesync dictionary
                post_data = util.fix_args(args, self.optional_args)

                if self.select_arg:
                    command_kwargs[self.select_arg] = \
                            post_data.pop(self.select_arg)

                if post_data or self.select_arg not in command_kwargs:
                    command_kwargs["post_data"] = post_data

                if args.get("--csv"):
                    command_kwargs["csv_format"] = True

                return command(**command_kwargs)

            else:
                if util.check_token_expiration(ts):
                    return {"error": "Your token has expired. Please sign in "
                                     "again"}

                return command()

        return wrapped_command


def connect(arg_url="", config_dict=dict(), test=False, interactive=True):
    """Creates a new pymesync.TimeSync instance with a new URL"""

    global ts

    url = ""

    # Set the global variable so we can reconnect later.
    # If the URL is in the config, use that value at program startup
    # If the URL is provided in command line arguments, use that value
    if arg_url:
        url = arg_url
    elif "timesync_url" in config_dict:
        url = config_dict["timesync_url"]
    elif interactive:
        url = util.get_field("URL of TimeSync server") if not test else "tst"
    else:
        return {"climesync error": "Couldn't connect to TimeSync. Is "
                                   "timesync_url set in ~/.climesyncrc?"}

    if interactive and not test:
        util.add_kv_pair("timesync_url", url)

    # Create a new instance and attempt to connect to the provided url
    ts = pymesync.TimeSync(baseurl=url, test=test)

    # No response from server upon connection
    return list()


def disconnect():
    """Disconnects from the TimeSync server"""

    global ts

    ts = None

    # No response from server
    return list()


def sign_in(arg_user="", arg_pass="", config_dict=dict(), interactive=True):
    """Attempts to sign in with user-supplied or command line credentials"""

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    username = ""
    password = ""

    # If username or password in config, use them at program startup.
    if arg_user:
        username = arg_user
    elif "username" in config_dict:
        username = config_dict["username"]
    elif interactive:
        username = util.get_field("Username")

    if arg_pass:
        password = arg_pass
    elif "password" in config_dict:
        password = config_dict["password"]
    elif interactive:
        password = util.get_field("Password", field_type="$")

    if not username or not password:
        return {"climesync error": "Couldn't authenticate with TimeSync. Are "
                                   "username and password set in "
                                   "~/.climesyncrc?"}

    if interactive and not ts.test:
        util.add_kv_pair("username", username)
        util.add_kv_pair("password", password)

    # Attempt to authenticate and return the server's response
    return ts.authenticate(username, password, "password")


def sign_out():
    """Signs out from TimeSync and resets command line credentials"""

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    url = ts.baseurl
    test = ts.test

    # Create a new instance connected to the same server as the last
    ts = pymesync.TimeSync(baseurl=url, test=test)

    # No response from server
    return list()


@climesync_command()
def create_time(post_data=None):
    """create-time

Usage: create-time [-h] <duration> <project> <activities> ...
                        [--date-worked=<date_worked>]
                        [--issue-uri=<issue_uri>]
                        [--notes=<notes>]

Arguments:
    <duration>    Duration of time entry
    <project>     Slug of project worked on
    <activities>  Slugs of activities worked on

Options:
    -h --help                    Show this help message and exit
    --date-worked=<date_worked>  The date of the entry [Default: today]
    --issue-uri=<issue_uri>      The URI of the issue on an issue tracker
    --notes=<notes>              Additional notes

Examples:
    climesync.py create-time 1h0m projectx docs design qa
`       --issue-uri=https//www.github.com/foo/projectx/issue/42

    climesync.py create-time 0h45m projecty design --notes="Designing the API"
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    # The data to send to the server containing the new time information
    if post_data is None:
        post_data = util.get_fields([(":duration",   "Duration"),
                                     ("project",     "Project slug"),
                                     ("!activities", "Activity slugs"),
                                     ("date_worked", "Date (yyyy-mm-dd)"),
                                     ("*issue_uri",  "Issue URI"),
                                     ("*notes",      "Notes")])

    # Today's date
    if post_data["date_worked"] == "today":
        post_data["date_worked"] = date.today().isoformat()

    # If activities was sent as a single item
    if isinstance(post_data["activities"], str):
        post_data["activities"] = [post_data["activities"]]

    # Use the currently authenticated user
    post_data["user"] = ts.user

    # Attempt to create a time and return the response
    return ts.create_time(time=post_data)


@climesync_command(select_arg="uuid", optional_args=True)
def update_time(post_data=None, uuid=None):
    """update-time

Usage: update-time [-h] <uuid> [--duration=<duration>]
                        [--project=<project>]
                        [--user=<user>]
                        [--activities=<activities>]
                        [--date-worked=<date worked>]
                        [--issue-uri=<issue uri>]
                        [--notes=<notes>]

Arguments:
    <uuid>  The UUID of the time to update

Options:
    -h --help                    Show this help message and exit
    --duration=<duration>        Duration of time entry
    --project=<project>          Slug of project worked on
    --user=<user>                New time owner
    --activities=<activities>    Slugs of activities worked on
    --date-worked=<date worked>  The date of the entry
    --issue-uri=<issue uri>      The URI of the issue on an issue tracker
    --notes=<notes>              Additional notes

Examples:
    climesync.py update-time 838853e3-3635-4076-a26f-7efr4e60981f
`       --activities="[dev planning code]" --date-worked=2016-06-15

    climesync.py update-time c3706e79-1c9a-4765-8d7f-89b4544cad56
`       --project=projecty --notes="Notes notes notes"
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    if uuid is None:
        uuid = util.get_field("UUID of time to update")

    # The data to send to the server containing revised time information
    if post_data is None:
        post_data = util.get_fields([("*:duration",   "Duration"),
                                     ("*project",     "Project slug"),
                                     ("*user",        "New user"),
                                     ("*!activities", "Activity slugs"),
                                     ("*date_worked", "Date (yyyy-mm-dd)"),
                                     ("*issue_uri",   "Issue URI"),
                                     ("*notes",       "Notes")])

    if "activities" in post_data and isinstance(post_data["activities"], str):
        post_data["activities"] = [post_data["activities"]]

    # Attempt to update a time and return the response
    return ts.update_time(uuid=uuid, time=post_data)


@climesync_command(optional_args=True)
def get_times(post_data=None, csv_format=False):
    """get-times

Usage: get-times [-h] [--user=<users>] [--project=<projects>]
                      [--activity=<activities>] [--start=<start date>]
                      [--end=<end date>] [--uuid=<uuid>]
                      [--include-revisions=<True/False>]
                      [--include-deleted=<True/False>]
                      [--csv]

Options:
    -h --help                         Show this help message and exit
    --user=<users>                    Filter by a list of users
    --project=<projects>              Filter by a list of project slugs
    --activity=<activities>           Filter by a list of activity slugs
    --start=<start date>              Filter by start date
    --end=<end date>                  Filter by end date
    --uuid=<uuid>                     Get a specific time by uuid
                                      (If included, all options except
                                      --include-revisions and
                                      --include-deleted are ignored
`   --include-revisions=<True/False>  Whether to include all time revisions
`   --include-deleted=<True/False>    Whether to include deleted times
    --csv                             Output the result in CSV format

Examples:
    climesync.py get-times

    climesync.py get-times --csv > times.csv

    climesync.py get-times --project=projectx --activity=planning
`       --user="[userone usertwo]"

    climesync.py get-times --uuid=12345676-1c9a-rrrr-bbbb-89b4544cad56
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    interactive = post_data is None

    # Optional filtering parameters to send to the server
    if post_data is None:
        post_data = util.get_fields([("*!user", "Submitted by users"),
                                     ("*!project", "Belonging to projects"),
                                     ("*!activity", "Belonging to activities"),
                                     ("*start", "Beginning on date"),
                                     ("*end", "Ending on date"),
                                     ("*?include_revisions", "Allow revised?"),
                                     ("*?include_deleted", "Allow deleted?"),
                                     ("*uuid", "By UUID")])

    if "user" in post_data and isinstance(post_data["user"], str):
        post_data["user"] = [post_data["user"]]

    if "project" in post_data and isinstance(post_data["project"], str):
        post_data["project"] = [post_data["project"]]

    if "activity" in post_data and isinstance(post_data["activity"], str):
        post_data["activity"] = [post_data["activity"]]

    if "start" in post_data:
        post_data["start"] = [post_data["start"]]

    if "end" in post_data:
        post_data["end"] = [post_data["end"]]

    # Attempt to query the server for times with filtering parameters
    times = ts.get_times(query_parameters=post_data)

    # If the response is free of errors, make the times human-readable
    if times and 'error' not in times[0] and 'pymesync error' not in times[0]:
        for time in times:
            time["duration"] = util.to_readable_time(time["duration"])
    elif interactive and not times:
        return {"note": "No times were returned"}

    # Optionally output to a CSV file
    if interactive:
        csv_path = util.ask_csv()

        if csv_path:
            util.output_csv(times, "time", csv_path)
    elif csv_format:
        util.output_csv(times, "time", None)
        return []

    return times


@climesync_command(optional_args=True)
def sum_times(post_data=None):
    """sum-times

Usage: sum-times [-h] <project> ... [--start=<start date>] [--end=<end date>]

Arguments:
    <project>  The project slugs of the projects to sum times for

Options:
    -h --help             Show this help message and exit
    --start=<start date>  The date to start summing times
    --end=<end date>      The date to end summing times

Examples:
    climesync.py sum-times projectx

    climesync.py sum-times projectx projecty --start=2016-06-01
    """

    if post_data is None:
        post_data = util.get_fields([("!project", "Project slugs"),
                                     ("*start", "Start date (yyyy-mm-dd)"),
                                     ("*end", "End date (yyyy-mm-dd)")])

    if isinstance(post_data["project"], str):
        post_data["project"] = [post_data["project"]]

    result = ts.get_times(post_data)

    try:
        for project in post_data["project"]:
            time_sum = 0

            for user_time in result:
                if project in user_time["project"]:
                    time_sum += user_time["duration"]

            minutes, seconds = divmod(time_sum, 60)
            hours, minutes = divmod(minutes, 60)

            print
            print "{}".format(project)
            print util.to_readable_time(time_sum)

        return list()
    except Exception as e:
        print e
        return result


@climesync_command(select_arg="uuid")
def delete_time(uuid=None):
    """delete-time

Usage: delete-time [-h] <uuid>

Arguments:
    <uuid>  The uuid of the time to delete

Options:
    -h --help  Show this help message and exit

Examples:
    climesync.py delete-time 12345676-1c9a-rrrr-bbbb-89b4544cad56
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    if uuid is None:
        uuid = util.get_field("Time UUID")
        really = util.get_field(u"Do you really want to delete {}?"
                                .format(uuid),
                                field_type="?")

        if not really:
            return list()

    return ts.delete_time(uuid=uuid)


@climesync_command(optional_args=True)
def create_project(post_data=None):
    """create-project (Site admins only)

Usage: create-project [-h] <name> <slugs> [(<username> <access_mode>) ...]
                           [--uri=<project_uri>]
                           [--default-activity=<default_activity>]

Arguments:
    <name>         The project name
    <slugs>        Unique slugs associated with this project
    <username>     The name of a user to add to the project
    <access_mode>  The permissions of a user to add to the project

Options:
    -h --help                              Show this help message and exit
    --uri=<project_uri>                    The project's URI
    --default-activity=<default_activity>  The slug of the default activity
                                           associated with this project

User permissions help:
    User permissions are entered in a similar format to *nix file permissions.
    Each possible permission is represented as a binary 0 or 1 in the following
    format where each argument is a binary 0 or 1:

    <member><spectator><manager>

    For example, to set a user's permission level to both member and manager
    this would be the permission number:

    <member = 1><spectator = 0><manager = 1> == 101 == 5

    So the entire command would be entered as:

    create-project <name> <slugs> <username> 5

Examples:
    climesync.py create-project "Project Z" "[pz projectz]"
`       userone 4 usertwo 5 userthree 7

    climesync.py create-project "Project Foo" foo userone 7
`       --uri=https://www.github.com/bar/foo --default-activity=planning
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    # The data to send to the server containing new project information
    if post_data is None:
        post_data = util.get_fields([("name", "Project name"),
                                     ("!slugs", "Project slugs"),
                                     ("*uri", "Project URI"),
                                     ("*!users", "Users"),
                                     ("*default_activity",
                                      "Default activity")])
    else:
        permissions_dict = dict(zip(post_data.pop("username"),
                                    post_data.pop("access_mode")))
        post_data["users"] = util.fix_user_permissions(permissions_dict)

    # If users have been added to the project, ask for user permissions
    if "users" in post_data and not isinstance(post_data["users"], dict):
        users = post_data["users"]
        post_data["users"] = util.get_user_permissions(users)

    if isinstance(post_data["slugs"], str):
        post_data["slugs"] = [post_data["slugs"]]

    # Attempt to create a new project and return the response
    return ts.create_project(project=post_data)


@climesync_command(select_arg="slug", optional_args=True)
def update_project(post_data=None, slug=None):
    """update-project (Site admins only)

Usage: update-project [-h] <slug> [(<username> <access_mode>) ...]
                           [--name=<project_name>]
                           [--slugs=<project_slugs>]
                           [--uri=<project_uri>]
                           [--default-activity=<default_activity>]

Arguments:
    <username>     The name of a user to add to the project
    <access_mode>  The permissions of a user to add to the project

Options:
    -h --help                              Show this help message and exit
    --name=<project_name>                  Updated project name
    --slugs=<project_slugs>                Updated list of project slugs
    --uri=<project_uri>                    Updated project's URI
    --default-activity=<default_activity>  Updated slug of the default activity
                                           associated with this project

User permissions help:
    User permissions are entered in a similar format to *nix file permissions.
    Each possible permission is represented as a binary 0 or 1 in the following
    format where each argument is a binary 0 or 1:

    <member><spectator><manager>

    For example, to set a user's permission level to both member and manager
    this would be the permission number:

    <member = 1><spectator = 0><manager = 1> == 101 == 5

    So the entire command would be entered as:

    update-project <name> <slugs> <username> 5

Examples:
    climesync.py update-project foo --name=Foobarbaz --slugs="[foo bar baz]"

    climesync.py update-project pz userone 7
`       --uri=https://www.github.com/bar/projectz
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    if slug is None:
        slug = util.get_field("Slug of project to update")

    # The data to send to the server containing revised project information
    if post_data is None:
        post_data = util.get_fields([("*name", "Updated project name"),
                                     ("*!slugs", "Updated project slugs"),
                                     ("*uri", "Updated project URI"),
                                     ("*!users", "Updated users"),
                                     ("*default_activity",
                                      "Updated default activity")])
    else:
        permissions_dict = dict(zip(post_data.pop("username"),
                                    post_data.pop("access_mode")))
        post_data["users"] = util.fix_user_permissions(permissions_dict)

    # If user permissions are going to be updated, ask for them
    if "users" in post_data and not isinstance(post_data["users"], dict):
        users = post_data["users"]
        post_data["users"] = util.get_user_permissions(users)

    if "slugs" in post_data and isinstance(post_data["slugs"], str):
        post_data["slugs"] = [post_data["slugs"]]

    # Attempt to update the project information and return the response
    return ts.update_project(project=post_data, slug=slug)


@climesync_command(optional_args=True)
def get_projects(post_data=None, csv_format=False):
    """get-projects

Usage: get-projects [-h] [--include-revisions=<True/False>]
                         [--include-deleted=<True/False>]
                         [--slug=<slug>]
                         [--csv]

Options:
    -h --help                         Show this help message and exit
    --include-revisions=<True/False>  Whether to include revised entries
    --include-deleted=<True/False>    Whether to include deleted entries
    --slug=<slug>                     Filter by project slug
    --csv                             Output the result in CSV format

Examples:
    climesync.py get-projects

    climesync.py get-projects --csv > projects.csv

    climesync.py get-projects --slug=projectx --include-revisions=True
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    interactive = post_data is None

    # Optional filtering parameters
    if post_data is None:
        post_data = util.get_fields([("*?include_revisions", "Allow revised?"),
                                     ("*?include_deleted", "Allow deleted?"),
                                     ("*slug", "By project slug")])

    # Attempt to query the server with filtering parameters
    projects = ts.get_projects(query_parameters=post_data)

    if interactive and not projects:
        return {"note": "No projects were returned"}

    if interactive:
        csv_path = util.ask_csv()

        if csv_path:
            util.output_csv(projects, "project", csv_path)
    elif csv_format:
        util.output_csv(projects, "project", None)
        return []

    return projects


@climesync_command(select_arg="slug")
def delete_project(slug=None):
    """delete-project (Site admins only)

Usage: delete-project [-h] <slug>

Arguments:
    <slug>  The slug of the project to delete

Options:
    -h --help  Show this help message and exit

Examples:
    climesync.py delete-project foo
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    if slug is None:
        slug = util.get_field("Project slug")
        really = util.get_field(u"Do you really want to delete {}?"
                                .format(slug),
                                field_type="?")

        if not really:
            return list()

    return ts.delete_project(slug=slug)


@climesync_command()
def create_activity(post_data=None):
    """create-activity (Site admins only)

Usage: create-activity [-h] <name> <slug>

Arguments:
    <name>  The name of the new activity
    <slug>  The slug of the new activity

Options:
    -h --help  Show this help message and exit

Examples:
    climesync.py create-activity Coding code

    climesync.py create-activity "Project Planning" planning
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    # The data to send to the server containing new activity information
    if post_data is None:
        post_data = util.get_fields([("name", "Activity name"),
                                     ("slug", "Activity slug")])

    # Attempt to create a new activity and return the response
    return ts.create_activity(activity=post_data)


@climesync_command(select_arg="old_slug", optional_args=True)
def update_activity(post_data=None, old_slug=None):
    """update-activity (Site admins only)

Usage: update-activity [-h] <old_slug> [--name=<name>] [--slug=<slug>]

Arguments:
    <old_slug>  The slug of the activity to update

Options:
    -h --help      Show this help message and exit
    --name=<name>  The updated activity name
    --slug=<slug>  The updated activity slug

Examples:
    climesync.py update-activity planning --name=Planning

    climesync.py update-activity code --slug=coding
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    if old_slug is None:
        old_slug = util.get_field("Slug of activity to update")

    # The data to send to the server containing revised activity information
    if post_data is None:
        post_data = util.get_fields([("*name", "Updated activity name"),
                                     ("*slug", "Updated activity slug")])

    # Attempt to update the activity information and return the repsonse
    return ts.update_activity(activity=post_data, slug=old_slug)


@climesync_command(optional_args=True)
def get_activities(post_data=None, csv_format=False):
    """get-activities

Usage: get-activities [-h] [--include-revisions=<True/False>]
                           [--include-deleted=<True/False>]
                           [--slug=<slug>]
                           [--csv]

Options:
    -h --help                         Show this help message and exit
    --include-revisions=<True/False>  Whether to include revised entries
    --include-deleted=<True/False>    Whether to include deleted entries
    --slug=<slug>                     Filter by activity slug
    --csv                             Output the result in CSV format

Examples:
    climesync.py get-activities

    climesync.py get-activities --csv > activities.csv

    climesync.py get-activities --include-deleted=True

    climesync.py get-activities --slug=planning
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    interactive = post_data is None

    # Optional filtering parameters
    if post_data is None:
        post_data = util.get_fields([("*?include_revisions", "Allow revised?"),
                                     ("*?include_deleted", "Allow deleted?"),
                                     ("*slug", "By activity slug")])

    # Attempt to query the server with filtering parameters
    activities = ts.get_activities(query_parameters=post_data)

    if interactive and not activities:
        return {"note": "No activities were returned"}

    if interactive:
        csv_path = util.ask_csv()

        if csv_path:
            util.output_csv(activities, "activity", csv_path)
    elif csv_format:
        util.output_csv(activities, "activity", None)
        return []

    return activities


@climesync_command(select_arg="slug")
def delete_activity(slug=None):
    """delete-activity (Site admins only)

Usage: delete-activity [-h] <slug>

Arguments:
    <slug>  The slug of the activity to delete

Options:
    -h --help  Show this help message and exit

Examples:
    climesync.py delete-activity planning
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    if slug is None:
        slug = util.get_field("Activity slug")
        really = util.get_field(u"Do you really want to delete {}?"
                                .format(slug),
                                field_type="?")

        if not really:
            return list()

    return ts.delete_activity(slug=slug)


@climesync_command(optional_args=True)
def create_user(post_data=None):
    """create-user (Site admins only)

Usage: create-user [-h] <username> <password> [--display-name=<display_name>]
                        [--email=<email>] [--site-admin=<True/False>]
                        [--site-manager=<True/False>]
                        [--site-spectator=<True/False>] [--meta=<metainfo>]
                        [--active=<True/False>]

Arguments:
    <username>  The username of the new user
    <password>  The password of the new user

Options:
    -h --help                      Show this help message and exit
    --display-name=<display_name>  The display name of the new user
    --email=<email>                The email address of the new user
    --site-admin=<True/False>      Whether the new user is a site admin
                                   [Default: False]
    --site-manager=<True/False>    Whether the new user is a site manager
                                   [Default: False]
    --site-spectator=<True/False>  Whether the new user is a site spectator
                                   [Default: False]
    --meta=<metainfo>              Extra user metainformation
    --active=<True/False>          Whether the new user is active
                                   [Default: True]

Examples:
    climesync.py create-user userfour pa$$word --display-name=4chan
`       --meta="Who is this 4chan?"

    climesync.py create-user anotheruser "correct horse battery staple"
`       --email=anotheruser@osuosl.org --site-admin=True
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    # The data to send to the server containing new user information
    if post_data is None:
        post_data = util.get_fields([("username", "New user username"),
                                     ("$password", "New user password"),
                                     ("*display_name", "New display name"),
                                     ("*email", "New user email"),
                                     ("*?site_admin", "Site admin?"),
                                     ("*?site_manager", "Site manager?"),
                                     ("*?site_spectator", "Site spectator?"),
                                     ("*meta", "Extra meta-information"),
                                     ("*?active", "Is the new user active?")])

    # Attempt to create a new user and return the response
    return ts.create_user(user=post_data)


@climesync_command(select_arg="old_username", optional_args=True)
def update_user(post_data=None, old_username=None):
    """update-user (Site admins only)

Usage: update-user [-h] <old_username> [--username=<username>]
                        [--password=<password>] [--display-name=<display_name>]
                        [--email=<email>] [--site-admin=<True/False>]
                        [--site-manager=<True/False>]
                        [--site-spectator=<True/False>] [--meta=<metainfo>]
                        [--active=<True/False>]

Arguments:
    <old_username>  The username of the user to update

Options:
    -h --help                      Show this help message and exit
    --username=<username>          The updated username of the user
    --password=<password>          The updated password of the user
    --display-name=<display_name>  The updated display name of the user
    --email=<email>                The updated email address of the user
    --site-admin=<True/False>      Whether the user is a site admin
    --site-manager=<True/False>    Whether the user is a site manager
    --site-spectator=<True/False>  Whether the user is a site spectator
    --meta=<metainfo>              Extra user metainformation
    --active=<True/False>          Whether the user is active

Examples:
    climesync.py update-user userfour --display-name="System Administrator"
`       --active=False --site-spectator=True

    climesync.py update-user anotheruser --username=newuser
`       --meta="Metainformation goes here" --site-admin=False
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    if old_username is None:
        old_username = util.get_field("Username of user to update")

    # The data to send to the server containing revised user information
    if post_data is None:
        post_data = util.get_fields([("*username", "Updated username"),
                                     ("*$password", "Updated password"),
                                     ("*display_name", "Updated display name"),
                                     ("*email", "Updated email"),
                                     ("*?site_admin", "Site admin?"),
                                     ("*?site_manager", "Site manager?"),
                                     ("*?site_spectator", "Site spectator?"),
                                     ("*meta", "New metainformation"),
                                     ("*?active", "Is the user active?")])

    # Attempt to update the user and return the response
    return ts.update_user(user=post_data, username=old_username)


@climesync_command(optional_args=True)
def get_users(post_data=None, csv_format=False):
    """get-users

Usage: get-users [-h] [--username=<username>] [--csv]

Options:
    -h --help              Show this help message and exit
    --username=<username>  Search for a user by username
    --csv                  Output the result in CSV format

Examples:
    climesync.py get-users

    climesync.py get-users --csv > users.csv

    climesync.py get-users userfour
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    interactive = post_data is None

    # Optional filtering parameters
    if post_data is None:
        post_data = util.get_fields([("*username", "Username")])

    # Using dict.get so that None is returned if the key doesn't exist
    username = post_data.get("username")

    # Attempt to query the server with filtering parameters
    users = ts.get_users(username=username)

    if interactive and not users:
        return {"note": "No users were returned"}

    if interactive:
        csv_path = util.ask_csv()

        if csv_path:
            util.output_csv(users, "user", csv_path)
    elif csv_format:
        util.output_csv(users, "user", None)
        return []

    return users


@climesync_command(select_arg="username")
def delete_user(username=None):
    """delete-user (Site admins only)

Usage: delete-user [-h] <username>

Arguments:
    <username>  The username of the user to delete

Options:
    -h --help  Show this help message and exit

Examples:
    climesync.py delete-user userfour
    """

    global ts

    if not ts:
        return {"error": "Not connected to TimeSync server"}

    if username is None:
        username = util.get_field("Username")
        really = util.get_field(u"Do you really want to delete {}?"
                                .format(username),
                                field_type="?")

        if not really:
            return list()

    return ts.delete_user(username=username)
