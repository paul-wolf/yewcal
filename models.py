import datetime
from enum import Enum

from typing import Dict, List, Optional, Final
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


