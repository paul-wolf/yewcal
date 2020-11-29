import os
import sys
import re

import arrow

from constants import CURRENT_TZ, DEFAULT_TZ_NAME, EVENTS_DATA_PATH


def dt_nowish(minutes):
    return arrow.get(arrow.get().shift(minutes=minutes)).to(CURRENT_TZ)

def dt_today():
    return arrow.get(arrow.get().date()).to(CURRENT_TZ)


def dt_tomorrow():
    return arrow.get(arrow.get().date()).shift(days=1).to(CURRENT_TZ)


def is_uuid(uid):
    """Return non-None if uid is a uuid."""
    uuidregex = re.compile(
        r"[0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12}\Z", re.I
    )
    return uuidregex.match(uid)


def is_short_uuid(s):
    """Return non-None if uid is a uuid."""
    uuid_short_regex = re.compile(r"[0-9a-f]{8}\Z", re.I)
    return uuid_short_regex.match(s)


def get_short_uid(s):
    return s.split("-")[0]
