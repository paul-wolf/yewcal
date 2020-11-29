import os
import sys
import re



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
