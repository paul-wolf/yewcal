import os
import sys

import arrow

import utils
from utils import dt_today, dt_tomorrow, dt_nowish

from constants import CURRENT_TZ, DEFAULT_TZ_NAME, EVENTS_DATA_PATH
from models import Repeats, CalendarEntry
from files import read_events, write_events
from services import slack

def notify_todays_events():
    events = read_events()
    events = list(filter(lambda e: e.dt >= dt_today() and e.dt < dt_tomorrow(), events))


def get_impending_events(events, minutes=10):
    """Get events happening within n minutes."""
    start = dt_nowish(0)
    end = dt_nowish(10)
    events = list(filter(lambda e: e.dt >= start and e.dt < end, events))
    return events

def notify_impending_events():
    events = read_events()
    events = get_impending_events(events, minutes=15)
    for e in events:
        slack.post_message_to_slack("#random", f"{e.summary} at {e.dt}")

        
