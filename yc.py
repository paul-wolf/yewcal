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
from utils import dt_today, dt_tomorrow

from constants import CURRENT_TZ, DEFAULT_TZ_NAME, EVENTS_DATA_PATH
from models import Repeats, CalendarEntry
from files import read_events, write_events
from notify import notify_impending_events, notify_todays_events
import sync
from services import google_api


def parse_datetime(dt_str):
    return dateparser.parse(dt_str)


def timezone_name_from_string(tz_str) -> str:
    """Return a timezone string.
    if we get a string like "London"
    return a string "Europe/London"
    """
    for tz in pytz.all_timezones:
        if "/" in tz_str:
            if tz_str.lower() == tz.lower():
                return tz
        else:
            if tz_str.lower() == tz.split("/")[-1].lower():
                return tz
    raise Exception("Cannot find timezone: {tz_str}")


def make_event(
    summary,
    dt_str,
    timezone_string,
    duration: Optional[datetime.timedelta] = None,
    external_id=None,
    source=None,
    data=None,
):
    """Create new calendar event."""
    if not timezone_string:
        timezone_string = DEFAULT_TZ_NAME
    timezone_string = timezone_name_from_string(timezone_string)
    tz = pytz.timezone(timezone_string)

    dt = parse_datetime(dt_str)
    if not dt.tzinfo:
        dt = tz.localize(dt)
    dt = dt.replace(microsecond=0)

    duration = duration if duration else datetime.timedelta(hours=1)

    ce = CalendarEntry(
        uid=str(uuid.uuid4()),
        user=getpass.getuser(),
        summary=summary,
        dt=dt,
        timezone=timezone_string,
        created=datetime.datetime.now(tz),
        updated=datetime.datetime.now(tz),
        duration=duration,
        repeats=Repeats.UNIQUE,
        external_id=external_id,
        source=source,
        data=data,
    )
    return ce


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


def print_events(events, human=None, numbered=None, use_local_time=True):
    for i, e in enumerate(events):
        if numbered:
            print(f"{str(i).ljust(3)})", end="")
        if not numbered:
            print(e.uid.split("-")[0].ljust(10), end="")
        dt = arrow.get(e.dt).to(CURRENT_TZ) if use_local_time else e.dt
        if human:
            print(arrow.get(dt).humanize().ljust(20), end="")
        else:
            print(str(dt).ljust(35), end="")
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
    if not summary:
        summary = "my summary"
        interactive = True
    if not dt:
        dt = dt_tomorrow().isoformat()
        interactive = True
    timezone = timezone if timezone else DEFAULT_TZ_NAME
    events = ctx.obj.get("events")
    e = make_event(summary, dt, timezone)
    if interactive:
        e = edit_event_interactive(e)
    upsert_event(e, events)
    write_events(events)
    e.dump()


def edit_event_interactive(event: CalendarEntry):
    summary = click.prompt("Summary", default=event.summary, type=str)
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


def filter_events(events, name):
    """Filter events with name."""
    if name.lower().strip() == "today":
        return list(filter(lambda e: e.dt.date() == arrow.get().date, events))


@cli.command()
@click.argument("name", required=False)
@click.pass_context
def edit(ctx, name):
    """Edit a calendar event."""

    events = ctx.obj.get("events")

    if utils.is_uuid(name):
        events = list(filter(lambda e: e.uid == name, events))
        if not events:
            click.echo("Could not find event")
            sys.exit(1)
        event = events[0]
    elif utils.is_short_uuid(name):
        events = list(filter(lambda e: utils.get_short_uid(e.uid) == name, events))
        if not events:
            click.echo("Could not find event")
            sys.exit(1)
        event = events[0]
    else:
        if name:
            events = filter_events(events, name)
            if not events:
                click.echo(f"Not events for {name}")
                sys.exit(1)
        if len(events) > 1:
            print_events(events, numbered=True)
            v = click.prompt("Choose an event", type=int)
            event = events[v]
        elif len(events) == 1:
            event = events[0]

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
def tomorrow(ctx, human):
    """Create a calendar event."""
    events = read_events()
    events = list(
        filter(
            lambda e: e.dt >= dt_tomorrow()
            and e.dt < arrow.get(dt_tomorrow()).shift(days=1),
            events,
        )
    )
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


@cli.command()
@click.pass_context
def notify_today(ctx):
    notify_todays_events()


@cli.command()
@click.option("--minutes", "-m", default=15, required=False)
@click.pass_context
def notify_soon(ctx, minutes):

    notify_impending_events(int(minutes))


@cli.command()
@click.pass_context
def push_events(ctx):
    sync.push_event_data()
    print("Events pushed")


@cli.command()
@click.pass_context
def pull_events(ctx):
    sync.get_event_data()
    print("Event data pulled")


def existing_external_event(external_id, events):
    """Return existing external event or None."""
    events = list(filter(lambda e: e.external_id == external_id, events))
    if len(events):
        return events[0]
    return None


@cli.command()
@click.pass_context
def pull_google_events(ctx):
    rejected = list()
    events = ctx.obj.get("events")
    gevents = google_api.get_google_events(10)
    for e in gevents:
        external_id = e.get("id")
        summary = e.get("summary")
        dt_start_str = (
            e.get("start")["dateTime"] if "dateTime" in e.get("start") else None
        )
        dt_end_str = e.get("end")["dateTime"] if "dateTime" in e.get("end") else None
        if dt_start_str and dt_end_str:
            dt_start = arrow.get(parse_datetime(dt_start_str))
            dt_end = arrow.get(parse_datetime(dt_end_str))
            duration = dt_end - dt_start
        tz_str = e.get("start")["timeZone"] if "timeZone" in e.get("start") else None
        data = e.get("conferenceData")
        existing_event = existing_external_event(e, events)
        if existing_event or external_id in rejected:
            print("skipping existing event: {existing_event}")
            continue
        print("")
        print(f"Summary     : {summary}")
        print(f"Start       : {dt_start_str}")
        print(f"Timezone    : {tz_str}")

        rejected.append(external_id)
        v = click.confirm("Take this event?")
        if v:
            print(
                f"TAKING: {summary=}, {dt_start_str=}, {duration=}, {tz_str=}, {external_id=}"
            )
            new_event = make_event(
                summary,
                dt_start_str,
                tz_str,
                duration=duration,
                external_id=external_id,
                source="googlecal",
                data=data,
            )
            upsert_event(new_event, events)
        else:
            print("SKIPPING")


if __name__ == "__main__":
    cli()
