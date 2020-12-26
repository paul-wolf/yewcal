import sys

import uuid

from typing import List, Optional
import pytz
import datetime
import getpass
import calendar

import click
import dateparser
import arrow

import utils
from utils import dt_today, dt_tomorrow

from constants import CURRENT_TZ, DEFAULT_TZ_NAME
import constants
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
) -> CalendarEntry:
    """Create and return new calendar event."""
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
    events = tuple(e for e in event_data if e.uid == event.uid)
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
    current_date = None
    print(f"Current time: {arrow.get()}, {constants.CURRENT_TZ}")
    for i, e in enumerate(events):
        # tz = pytz.timezone(e.timezone)
        if not current_date == e.dt.date():
            day_string = arrow.get(arrow.get(e.dt).date()).format("ddd YYYY-MM-DD")
            current_date = e.dt.date()
            click.echo(day_string.ljust(16), nl=False)
        else:
            print("".ljust(16), end="")

        if numbered:
            print(f"{str(i).ljust(3)})", end="")
        if not numbered:
            print(e.uid.split("-")[0].ljust(10), end="")

        # print time
        dt = (
            arrow.get(e.dt.astimezone(constants.CURRENT_TZ))
            if use_local_time
            else arrow.get(e.dt)
        )
        if human:
            click.echo(
                click.style(arrow.get(dt).humanize().ljust(16), fg="blue"), nl=False
            )
        else:
            dtf = dt.format("HH:mm")
            print(dtf.ljust(8), end="")

        click.echo(click.style(e.summary[:20].ljust(22), fg="green"), nl=False)

        tz_string = f"[{arrow.get(e.dt).format('HH:mm')} {e.timezone}]"
        print(tz_string.ljust(22), end="")
        print(str(e.duration).ljust(10), end="")
        if not e.repeats == Repeats.UNIQUE:
            print(str(e.repeats).ljust(10), end="")
        print()


@click.group()
@click.option("--user", help="User name", required=False)
@click.option("--debug", "-d", is_flag=True, help="Debug flag", required=False)
@click.pass_context
def cli(ctx, user, debug):
    ctx.ensure_object(dict)
    events = read_events()
    ctx.obj["events"] = sorted(events, key=lambda c: c.dt)


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


def edit_event_interactive(event: CalendarEntry) -> CalendarEntry:
    """Interactively query the user for the event data.

    This returns an event object but does not save it.
    """
    summary = click.prompt("Summary", default=event.summary, type=str)
    year = click.prompt("Year", default=event.dt.now().year, type=int)
    month = click.prompt("Month", default=event.dt.month, type=int)
    day = click.prompt("Day", default=event.dt.day, type=int)
    hour = click.prompt("Hour", default=event.dt.hour, type=int)
    minute = click.prompt("Minute", default=event.dt.minute, type=int)
    timezone_str = click.prompt("Timezone", default=event.timezone, type=str)
    # duration = click.prompt("Duration", default=event.duration, type=str)

    # import ipdb;ipdb.set_trace()

    event.summary = summary
    timezone_str = timezone_name_from_string(timezone_str)
    tz = pytz.timezone(timezone_str)
    event.dt = tz.localize(
        datetime.datetime(int(year), int(month), int(day), int(hour), int(minute))
    )
    event.timezone = timezone_str

    return event


def filter_events(events, name):
    """Filter events with name."""
    if name.lower().strip() == "today":
        return tuple(e for e in events if e.dt.date() == arrow.get().date)


def get_event(events, name: str) -> CalendarEntry:
    event = None
    if utils.is_uuid(name):
        events = tuple(e for e in events if e.uid == name)
        if not events:
            click.echo("Could not find event")
            sys.exit(1)
        event = events[0]
    elif utils.is_short_uuid(name):
        events = tuple(e for e in events if utils.get_short_uid(e.uid) == name)
        if not events:
            click.echo("Could not find event")
            sys.exit(1)
        event = events[0]
    else:
        if name:
            events = filter_events(events, name)
            if not events:
                click.echo(f"No events for {name}")
                sys.exit(1)
        if len(events) > 1:
            print_events(events, numbered=True)
            v = click.prompt("Choose an event", type=int)
            event = events[v]
        elif len(events) == 1:
            event = events[0]
    return event


@cli.command()
@click.argument("name", required=False)
@click.pass_context
def edit(ctx, name):
    """Edit a calendar event."""

    events = ctx.obj.get("events")

    event = get_event(events, name)
    event = edit_event_interactive(event)
    upsert_event(event, events)
    write_events(events)
    event.dump()


@cli.command()
@click.argument("name", required=False)
@click.pass_context
def describe(ctx, name):
    """Show detail about a calendar event."""

    events = ctx.obj.get("events")
    event = get_event(events, name)
    event.dump()


@cli.command()
@click.option("--human", "-h", is_flag=True, required=False)
@click.option("--local", "-l", is_flag=True, default=True, required=False)
@click.pass_context
def today(ctx, human, local):
    """Show today's events."""
    events = ctx.obj.get("events")
    events = tuple(e for e in events if e.dt >= dt_today() and e.dt < dt_tomorrow())
    print_events(events, human, use_local_time=local)


@cli.command()
@click.option("--human", "-h", is_flag=True, required=False)
@click.option("--local", "-l", is_flag=True, default=True, required=False)
@click.pass_context
def tomorrow(ctx, human, local):
    """Show tomorrow's events."""
    events = ctx.obj.get("events")

    events = (
        e
        for e in events
        if e.dt >= dt_tomorrow() and e.dt < arrow.get(dt_tomorrow()).shift(days=1)
    )
    print_events(events, human, use_local_time=local)


@cli.command()
@click.option("--human", "-h", is_flag=True, required=False)
@click.option("--local", "-l", is_flag=True, default=True, required=False)
@click.pass_context
def future(ctx, human, local):
    """Show all future events."""

    events = ctx.obj.get("events")
    events = tuple(e for e in events if e.dt >= dt_today())
    print_events(events, human, use_local_time=local)


@cli.command()
@click.option("--human", "-h", is_flag=True, required=False)
@click.option("--local", "-l", is_flag=True, default=True, required=False)
@click.pass_context
def all(ctx, human, local):
    """List all events, past and future."""
    events = ctx.obj.get("events")
    print_events(events, human, use_local_time=local)


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
    """Show calendar for months."""
    dt = datetime.datetime.today()
    calendar.prmonth(dt.year, dt.month)


@cli.command()
@click.pass_context
@click.argument("dt_str")
def check(ctx, dt_str):
    """Show how a data string will be interpreted."""
    print(parse_datetime(dt_str).isoformat())


@cli.command()
@click.pass_context
def notify_today(ctx):
    """Show today's events."""
    notify_todays_events()


@cli.command()
@click.option("--minutes", "-m", default=15, required=False)
@click.pass_context
def notify_soon(ctx, minutes):
    """Process notifications for imminent events."""
    notify_impending_events(int(minutes))


@cli.command()
@click.pass_context
def push_events(ctx):
    """Push event data to remote storage."""
    sync.push_event_data()
    print("Events pushed")


@cli.command()
@click.pass_context
def pull_events(ctx):
    """Pull event data from remote storage. Overwrites local data."""
    sync.get_event_data()
    print("Event data pulled")


@cli.command()
@click.pass_context
def info(ctx):
    """Show information about settings."""
    click.echo(f"{constants.BASE_DATA_PATH=}")
    click.echo(f"{constants.EVENTS_FILENAME=}")
    click.echo(f"{constants.CURRENT_TZ=}")
    click.echo(f"{constants.DEFAULT_TZ_NAME=}")


def existing_external_event(external_id, events) -> Optional[CalendarEntry]:
    """Return existing external event or None."""
    events = tuple(e for e in events if e.external_id == external_id)
    if len(events):
        return events[0]
    return None


@cli.command()
@click.pass_context
def pull_google_events(ctx):
    """Interactively pull data from user's google calendar.
    Requires credentials to be setup.
    """
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
