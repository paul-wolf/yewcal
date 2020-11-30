import os
import sys

import arrow

import utils
from utils import dt_today, dt_tomorrow, dt_nowish

from constants import CURRENT_TZ, DEFAULT_TZ_NAME, EVENTS_DATA_PATH, MY_EMAIL_ADDRESS
from models import Repeats, CalendarEntry
from files import read_events, write_events
from services import slack, mailgun


def events_as_string(events):
    s = ""
    for e in events:
        s += f"{e.dt.hour}:{e.dt.minute} {e.summary}\n"
    return s


def notify_todays_events():
    events = read_events()
    events = list(filter(lambda e: e.dt >= dt_today() and e.dt < dt_tomorrow(), events))
    body = events_as_string(events)
    r = mailgun.send_email(
        to_addresses=[MY_EMAIL_ADDRESS], subject="Today's events", body=body
    )
    print(r)
    if not r.status_code == 200:
        print(r.content)


def get_impending_events(events, minutes=15):
    """Get events happening within n minutes."""
    start = dt_nowish(0)
    end = dt_nowish(minutes)
    events = list(filter(lambda e: e.dt >= start and e.dt < end, events))
    return events


def notify_impending_events(minutes=15):
    events = read_events()
    events = get_impending_events(events, minutes)
    for e in events:
        slack.post_message_to_slack("#random", f"{e.summary} at {e.dt}")
