import os
import json
import unittest
import shutil
import datetime

from click.testing import CliRunner

import constants
from yc import cli
from yc import make_event, timezone_name_from_string, upsert_event, print_events
from yc import DatetimeInvalid
from files import write_events
import utils

TEST_USERNAME = "_cal_test_user_"


SETTINGS = {
    "AWS_ACCESS_KEY_ID": "asdfasdfasdfa",
    "AWS_SECRET_ACCESS_KEY": "asdfalsdjfal;sdfjalsdkjfa;sdl",
    "MG_API_KEY": "asdfasdfasdfasdfasdf",
    "MG_API_URL": "https://api.mailgun.net/v3/mg.yew.io",
    "MG_FROM": "info@yew.io",
    "SLACK_TOKEN": "xoxp-234234324-234234-234532342-asdfasdfsadf",
    "SLACK_API_URL": "https://slack.com/api",
    "MY_EMAIL_ADDRESS": "blah@blah.com",
    "MY_MOBILE": "+4412345678",
    "BUCKET": "yew-calll",
    "TWILIO_ACCOUNT_SID": "adsfasdfsadfasdfadsf",
    "TWILIO_AUTH_TOKEN": "asdfasdfasdfadsfasdfd",
    "TWILIO_ORIGIN_NUMBER": "+123456789",
}


class TestSum(unittest.TestCase):
    def setUp(self):
        self.username = TEST_USERNAME
        base_data_path = os.path.join(
            os.path.expanduser("~"), ".yew.d", self.username, "cal"
        )
        events_data_path = os.path.join(base_data_path, constants.EVENTS_FILENAME)
        self.events_data_path = events_data_path        
        settings_path = os.path.join(base_data_path, constants.SETTINGS_FILENAME)

        # we delete entire environment for each test
        # you really would not want to make a mistake here
        if os.path.exists(base_data_path):
            shutil.rmtree(base_data_path)
        os.makedirs(base_data_path)
        with open(settings_path, "wt") as f:
            f.write(json.dumps(SETTINGS))
        events = list()
        events.append(make_event("event1", "tomorrow",
                                 timezone_string="london",
                                 duration=datetime.timedelta(hours = 1),
                                 external_id="my_external_id",
                                 source="some_external_source",
                                 data={"mydata": "could be anything"}
                                 ))
        events.append(make_event("event2", "next week"))
        events.append(make_event("event3", "in four days"))
        events.append(make_event("event4", "today"))
        str(events[0])
        self.events = events
        self.event_count = len(events)
        write_events(events_data_path, events)


    def test_timezone_name_from_string(self):
        assert timezone_name_from_string("Pacific/Kwajalein")
        assert timezone_name_from_string("pacific/kwajalein")
        assert timezone_name_from_string("kwajalein")
        
    def test_invalid_timezone_name_from_string(self):
        with self.assertRaises(Exception):
            timezone_name_from_string("xxxxxxxxx")

    def test_util_dt_nowish(self):
        utils.dt_nowish(minutes=10)

    def test_upsert_event(self):
        upsert_event(self.events_data_path, self.events[0], self.events)

    def test_print_events(self):
        print_events(self.events, human=True, numbered=True, use_local_time=False)
        print_events(self.events, human=False, numbered=True, use_local_time=True)
        
    def test_edit(self):

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                f"--user={TEST_USERNAME}",
                "edit",
                self.events[0].uid,
            ],
            input="\n\n\n\n\n\n\n"
        )

        assert result.exit_code == 0
        
    def test_info(self):

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                f"--user={TEST_USERNAME}",
                "info",
            ],
        )

        assert result.exit_code == 0
        assert "DEFAULT_TZ_NAME" in result.output

    def test_invalid_datetime(self):
        with self.assertRaises(DatetimeInvalid):
            make_event("event invalid dt", "this is no datetime")

    def test_future(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                f"--user={self.username}",
                "future",
            ],
        )
        assert len(result.output.strip().split("\n")) == (self.event_count + 1)
        assert result.exit_code == 0

    def test_all(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                f"--user={self.username}",
                "all",
            ],
        )
        assert len(result.output.strip().split("\n")) == (self.event_count + 1)
        assert result.exit_code == 0

    def test_today(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                f"--user={self.username}",
                "today",
            ],
        )
        assert len(result.output.strip().split("\n")) == 2
        assert result.exit_code == 0

    def test_cal(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                f"--user={self.username}",
                "cal",
            ],
        )
        assert result.exit_code == 0

    def test_describe(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                f"--user={self.username}",
                "describe",
                self.events[0].uid,
            ],
        )
        assert result.exit_code == 0
        
    def test_describe_short_uid(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                f"--user={self.username}",
                "describe",
                self.events[0].uid.split("-")[0],
            ],
        )
        assert result.exit_code == 0

    def test_tz(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                f"--user={self.username}",
                "tz",
            ],
        )
        assert result.exit_code == 0

    def test_check(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                f"--user={self.username}",
                "check",
                "today",
            ],
        )
        assert result.exit_code == 0

    def test_create_event(self):
        runner = CliRunner()
        result = runner.invoke(
            cli, [f"--user={self.username}", "create", "test create event", "tomorrow"]
        )
        assert result.exit_code == 0

    # edit
    # notify-soon
    # notify-today
    # pull-events
    # pull-google-events
    # push-events

