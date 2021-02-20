import os
import json
import unittest
from unittest import mock
import shutil
import datetime
import types

from click.testing import CliRunner
from hypothesis import given
import hypothesis.strategies as st
from hypothesis import settings, Verbosity


import constants
from yc import cli
from yc import (
    make_event,
    timezone_name_from_string,
    upsert_event,
    print_events,
    get_event,
)
from yc import DatetimeInvalid, EventNotFound
from models import CalendarEntry
from files import write_events, read_events
import utils
import notify
from services import twilio
import sync

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


class TestYewCal(unittest.TestCase):
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
        events.append(
            make_event(
                "event1",
                "tomorrow",
                timezone_string="london",
                duration=datetime.timedelta(hours=1),
                external_id="my_external_id",
                source="some_external_source",
                data={"mydata": "could be anything"},
            )
        )
        events.append(make_event("event2", "next week"))
        events.append(make_event("event3", "in four days"))
        events.append(make_event("event4", "today"))

        self.events = events
        self.event_count = len(events)
        write_events(events_data_path, events)
        self.context = {
            "events_data_path": events_data_path,
        }
        self.context.update(SETTINGS)

    @given(
        st.text(min_size=2, max_size=1000),
        st.datetimes(),
        st.timezones(),
        st.timedeltas(),
    )
    # @settings(verbosity=Verbosity.verbose)
    def test_make_event(self, summary, dts, tz, delta):
        ce = make_event(
            summary=summary,
            dt_str=dts.isoformat(),
            timezone_string=str(tz),
            duration=delta,
        )
        assert isinstance(ce, CalendarEntry)
        assert ce.summary == summary

    # external_id=None,
    # source=None,
    # data=None,

    def test_str_event(self):
        assert str(self.events[0])

    def test_repr_event(self):
        assert repr(self.events[0])

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
        # write to events file with existing event
        upsert_event(self.events_data_path, self.events[0], self.events)
        events = read_events(self.events_data_path)
        assert len(events) == len(self.events)
        old_length = len(self.events)

        ce = make_event("upserted event", "next week")
        upsert_event(self.events_data_path, ce, self.events)
        events = read_events(self.events_data_path)
        assert len(events) == old_length + 1

    def test_print_events(self):
        print_events(self.events, human=True, numbered=True, use_local_time=False)
        print_events(self.events, human=False, numbered=True, use_local_time=True)

    def test_impending_events(self):
        events = notify.get_impending_events(self.events, minutes=10000)
        assert events

    def test_events_as_string(self):
        s = notify.events_as_string(self.events)
        assert s

    def test_notify_todays_events(self):
        with mock.patch("requests.post") as requests_post:
            requests_post.return_value = types.SimpleNamespace(
                status_code=200, content="ok"
            )
            r = notify.notify_todays_events(self.context)
            print(r)
            assert r.content == "ok"

    def test_notify_impending_events(self):
        with mock.patch("requests.post") as requests_post:
            requests_post.return_value = types.SimpleNamespace(
                status_code=200, content="ok", json=lambda: {"status": "ok"}
            )
            notify.notify_impending_events(self.context, minutes=10000)

    def test_twilio(self):
        with mock.patch("services.twilio.Client"):
            twilio.send_sms(self.context, "my message")

    @mock.patch("sync.get_s3")
    @mock.patch("sync.arrow.get")
    def test_get_event_data(self, mock_arrow_get, mock_get_s3):
        mock_arrow_get.return_value = datetime.datetime.now()
        sync.get_event_data(self.context)

    def test_get_event(self):
        # use short form of uuid
        assert get_event(self.events, self.events[0].uid.split("-")[0])
        # long form
        assert get_event(self.events, self.events[0].uid)
        # by name
        assert get_event(self.events, "event1")

    def test_get_event_not_found(self):
        with self.assertRaises(EventNotFound):
            get_event(self.events, "never heard of it")

    def test_edit(self):

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                f"--user={TEST_USERNAME}",
                "edit",
                self.events[0].uid,
            ],
            input="\n\n\n\n\n\n\n",
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

    # notify-soon
    # notify-today
    # pull-events
    # pull-google-events
    # push-events
