import datetime
import json
from enum import Enum

from typing import Dict, Optional
from pydantic import BaseModel


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
    external_id: Optional[str]  # google, ical, etc. id
    source: Optional[str]  # when we pull from another calendar
    data: Optional[Dict]  # arbitrary extra data like conference url

    def dump(self):
        print(f"uid     : {self.uid}")
        print(f"user    : {self.user}")
        print(f"dt      : {self.dt.isoformat()}")
        print(f"timezone: {self.timezone}")
        print(f"summary : {self.summary}")
        print(f"duration: {self.duration}")
        print(f"repeats : {self.repeats}")
        if self.source or self.external_id:
            print(f"source  : {self.source}")
            print(f"ext id  : {self.external_id}")
        if self.data:
            print(json.dumps(self.data, indent=4, default=str))

    def __str__(self):
        return f"{self.user}: {self.dt}, {self.summary}"

    def __repr__(self):
        return f"{self.user}: {self.dt}, {self.summary}"
