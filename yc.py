import os
import sys
import uuid
import json
from typing import Dict, List, Optional, Final
import pytz
from enum import Enum
import datetime
import getpass
import calendar

import pendulum
import click
import dateparser
from pydantic import BaseModel
import arrow

CURRENT_TZ = (
    datetime.datetime.now(datetime.timezone(datetime.timedelta(0))).astimezone().tzinfo
)
DEFAULT_TZ_NAME: Final = CURRENT_TZ.tzname(datetime.datetime.now())
EVENTS_DATA_PATH: Final = "data/events.json"


class Repeats(Enum):
    UNIQUE = 0
    HOURLY = 1
    DAILY = 2
    WEEKLY = 3
    MONTHLY = 4
    YEARLY = 5


class CalendarEntry(BaseModel):
    uid: str
    user: str  # local os username
    dt: datetime.datetime
    created: datetime.datetime
    updated: datetime.datetime
    summary: str
    description: Optional[str]
    duration: datetime.timedelta
    timezone: str
    repeats: Repeats

    def serialize(self):
        return {
            "uid": self.uid,
            "user": self.user,
            "dt": self.dt.isoformat(),
            "updated": self.updated.isoformat(),
            "created": self.created.isoformat(),
            "summary": self.summary,
            "description": self.description,
            "duration": self.duration.as_timedelta(),
            "timezone": self.timezone,
            "repeats": self.repeats,
        }

    def dump(self):
        print(f"uid: {self.uid}")
        print(f"user: {self.user}")
        print(f"dt: {self.dt.isoformat()}")
        print(f"summary: {self.summary}")

    def __str__(self):
        return f"{self.user}: {self.dt}, {self.summary}"

    def __repr__(self):
        return f"{self.user}: {self.dt}, {self.summary}"


def dt_today():
    return arrow.get(arrow.get().date()).to(CURRENT_TZ)


def dt_tomorrow():
    return arrow.get(arrow.get().date()).shift(days=1).to(CURRENT_TZ)


def parse_datetime(dt_str):
    return dateparser.parse(dt_str)


def timezone_name_from_string(tz_str):
    for tz in pytz.all_timezones:
        if "/" in tz_str:
            if tz_str.lower() == tz.lower():
                return tz
        else:
            if tz_str.lower() == tz.split("/")[-1].lower():
                return tz
    raise Exception("Cannot find timezone: {tz_str}")


def make_new_event(summary, dt_str, timezone_string):
    """Create new calendar event."""
    timezone_string = timezone_name_from_string(timezone_string)
    tz = pytz.timezone(timezone_string)

    dt = parse_datetime(dt_str)
    if not dt.tzinfo:
        dt = tz.localize(dt)
    dt = dt.replace(microsecond=0)

    ce = CalendarEntry(
        uid=str(uuid.uuid4()),
        user=getpass.getuser(),
        summary=summary,
        dt=dt,
        timezone=timezone_string,
        created=datetime.datetime.now(tz),
        updated=datetime.datetime.now(tz),
        duration=pendulum.duration(hours=1).as_timedelta(),
        repeats=Repeats.UNIQUE,
    )
    return ce


def read_events():
    if not os.path.exists(EVENTS_DATA_PATH):
        return list()
    with open(EVENTS_DATA_PATH) as f:
        s = f.read()
        if not s:
            return list()
        data = json.loads(s)
        return [CalendarEntry.parse_obj(d) for d in data]


def write_events(event_data):
    events = [json.loads(e.json()) for e in event_data]
    with open(EVENTS_DATA_PATH, "wt") as f:
        f.write(json.dumps(events))


def upsert_event(event, event_data):
    """Update or add event."""
    events = list(filter(lambda e: e.uid == event.uid, event_data))
    if events:
        # update existing
        event = events[0]
        event.summary = e.summary
        event.updated = pendulum.now(ce.timezone)
        event.duration = e.duration
        event.repeats = e.repeats
    else:
        # create new
        event_data.append(event)
    write_events(event_data)


def print_events(events, human=None):
    for e in events:
        print(e.uid.split("-")[0].ljust(10), end="")
        if human:
            print(arrow.get(e.dt).humanize().ljust(20), end="")
        else:
            print(str(e.dt).ljust(35), end="")
        print(e.summary[:20].ljust(22), end="")
        print(e.timezone.ljust(15), end="")
        print(str(e.duration).ljust(10), end="")
        print(str(e.repeats).ljust(10), end="")
        print()


@click.group()
@click.option("--user", help="User name", required=False)
@click.option("--debug", "-d", is_flag=True, help="Debug flag", required=False)
@click.pass_context
def cli(ctx, user, debug):
    ctx.ensure_object(dict)
    ctx.obj["events"] = read_events()


@cli.command()
@click.argument("summary", required=False)
@click.argument("dt", required=False)
@click.option("--timezone", "-t", required=False)
@click.pass_context
def create(ctx, summary, dt, timezone):
    """Create a calendar event."""
    timezone = timezone if timezone else DEFAULT_TZ_NAME
    events = ctx.obj.get("events")
    #  import ipdb; ipdb.set_trace()
    e = make_new_event(summary, dt, timezone)
    upsert_event(e, events)
    write_events(events)
    e.dump()


@cli.command()
@click.argument("name", required=False)
@click.pass_context
def edit(ctx, name):
    """Edit a calendar event."""

    events = ctx.obj.get("events")
    #  import ipdb; ipdb.set_trace()
    e = make_new_event(summary, dt, timezone)
    upsert_event(e, events)
    write_events(events)
    e.dump()


@cli.command()
@click.option("--human", "-h", is_flag=True, required=False)
@click.pass_context
def today(ctx, human):
    """Create a calendar event."""
    events = read_events()
    events = list(filter(lambda e: e.dt >= dt_today() and e.dt < dt_tomorrow(), events))
    print_events(events, human)


@cli.command()
@click.option("--human", "-h", is_flag=True, required=False)
@click.pass_context
def future(ctx, human):
    """Create a calendar event."""
    events = read_events()
    events = list(filter(lambda e: e.dt >= dt_today(), events))
    print_events(events, human)


@cli.command()
@click.option("--human", "-h", is_flag=True, required=False)
@click.pass_context
def all(ctx, human):
    """List all."""
    events = read_events()
    print_events(events, human)


@cli.command()
@click.pass_context
@click.argument("name", required=False)
def tz(ctx, name):
    """List all timezones."""
    for tz in pytz.all_timezones:
        if name:
            if name.lower() in tz.lower():
                print(tz)
        else:
            print(tz)


@cli.command()
@click.pass_context
@click.argument("months", required=False)
def cal(ctx, months):
    dt = datetime.datetime.today()
    calendar.prmonth(dt.year, dt.month)


if __name__ == "__main__":
    cli()
