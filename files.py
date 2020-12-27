import os
import json
from typing import List, Sequence


from models import CalendarEntry


def read_events(events_data_path) -> List[CalendarEntry]:
    if not os.path.exists(events_data_path):
        return list()
    with open(events_data_path) as f:
        s = f.read()
        if not s:
            return list()
        data = json.loads(s)
        return [CalendarEntry.parse_obj(d) for d in data]


def write_events(events_data_path, event_data: Sequence[CalendarEntry]) -> None:
    base_data_path = os.path.split(events_data_path)[0]
    if not os.path.exists(base_data_path):
        os.makedirs(base_data_path)
    events = [json.loads(e.json()) for e in event_data]
    with open(events_data_path, "wt") as f:
        f.write(json.dumps(events))
