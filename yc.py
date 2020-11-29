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

import utils

from constants import CURRENT_TZ, DEFAULT_TZ_NAME, EVENTS_DATA_PATH

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


def make_event(summary, dt_str, timezone_string):
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



def read_events() -> List[CalendarEntry]:
    if not os.path.exists(EVENTS_DATA_PATH):
        return list()
    with open(EVENTS_DATA_PATH) as f:
        s = f.read()
        if not s:
            return list()
        data = json.loads(s)
        return [CalendarEntry.parse_obj(d) for d in data]


def write_events(event_data: List[CalendarEntry]) -> None:
    events = [json.loads(e.json()) for e in event_data]
    with open(EVENTS_DATA_PATH, "wt") as f:
        f.write(json.dumps(events))


def upsert_event(event: CalendarEntry, event_data: List[CalendarEntry]):
    """Update or add event."""
    events = list(filter(lambda e: e.uid == event.uid, event_data))
    if events:
        # update existing
        e = events[0]
        e.summary = event.summary 
        e.description = event.description       
        e.updated = datetime.datetime.now(CURRENT_TZ)
        e.duration = event.duration
        e.repeats = event.repeats
    else:
        # create new
        event_data.append(event)
    write_events(event_data)


def print_events(events, human=None, numbered=None):
    for i, e in enumerate(events):
        if numbered:
            print(f"{str(i).ljust(3)})", end="")
        if not numbered:
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
@click.option("--interactive", "-i", required=False)
@click.pass_context
def create(ctx, summary, dt, timezone, interactive):
    """Create a calendar event."""
    timezone = timezone if timezone else DEFAULT_TZ_NAME
    events = ctx.obj.get("events")
    e = make_event(summary, dt, timezone)
    if interactive:
        e = edit_event_interactive(e)
    upsert_event(e, events)
    write_events(events)
    e.dump()


def edit_event_interactive(event:CalendarEntry):
    summary = click.prompt(f"Summary", default=event.summary, type=str)
    year = click.prompt("Year", default=event.dt.now().year, type=int)
    month = click.prompt("Month", default=event.dt.month, type=int)
    day = click.prompt("Day", default=event.dt.day, type=int)
    hour = click.prompt("Hour", default=event.dt.hour, type=int)
    minute = click.prompt("Minute", default=event.dt.minute, type=int)
    timezone_str = click.prompt("Timezone", default=event.timezone, type=str)
    # duration = click.prompt("Duration", default=event.duration, type=str)
    

    event.summary = summary
    timezone_str = timezone_name_from_string(timezone_str)
    tz = pytz.timezone(timezone_str)    
    event.dt = tz.localize(datetime.datetime(year, month, day, hour, minute))
    
    return event

@cli.command()
@click.argument("name", required=False)
@click.pass_context
def edit(ctx, name):
    """Edit a calendar event."""

    events = ctx.obj.get("events")
    print_events(events, numbered=True)
    v = click.prompt("Choose an event", type=int)
    event = events[v]
    event = edit_event_interactive(event)
    upsert_event(event, events)
    write_events(events)
    event.dump()


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

@cli.command()
@click.pass_context
@click.argument("dt_str")
def check(ctx, dt_str):
    print(parse_datetime(dt_str).isoformat())


if __name__ == "__main__":
    cli()
