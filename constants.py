import datetime

SETTINGS_FILENAME = "settings.json"
EVENTS_FILENAME = "events.json"

CURRENT_TZ = (
    datetime.datetime.now(datetime.timezone(datetime.timedelta(0))).astimezone().tzinfo
)
DEFAULT_TZ_NAME = CURRENT_TZ.tzname(datetime.datetime.now())  # type: ignore
