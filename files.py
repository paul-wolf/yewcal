import os
import json
from typing import List

from constants import EVENTS_DATA_PATH, BASE_DATA_PATH
from models import CalendarEntry


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
    if not os.path.exists(BASE_DATA_PATH):
        os.makedirs(BASE_DATA_PATH)
    events = [json.loads(e.json()) for e in event_data]
    with open(EVENTS_DATA_PATH, "wt") as f:
        f.write(json.dumps(events))
