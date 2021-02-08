import os

from utils import dt_today, dt_tomorrow, dt_nowish
from files import read_events
from services import slack, mailgun


def notify_macos(title, text):
    os.system(f"osascript -e 'display notification '{text}' with title '{title}'")


def events_as_string(events):
    s = ""
    for e in events:
        s += f"{e.dt.hour}:{e.dt.minute} {e.summary}\n"
    return s


def notify_todays_events(context):
    events = read_events(context["events_data_path"])
    events = tuple(e for e in events if e.dt >= dt_today() and e.dt < dt_tomorrow())
    body = events_as_string(events)
    r = mailgun.send_email(
        context,
        to_addresses=[context["MY_EMAIL_ADDRESS"]],
        subject="Today's events",
        body=body,
    )

    if not r.status_code == 200:
        print(r.content)
    return r


def get_impending_events(events, minutes=15):
    """Get events happening within n minutes."""
    start = dt_nowish(0)
    end = dt_nowish(minutes)
    events = tuple(e for e in events if e.dt >= start and e.dt < end)
    return events


def notify_impending_events(context, minutes=15):
    events = read_events(context["events_data_path"])
    events = get_impending_events(events, minutes)
    for e in events:
        slack.post_message_to_slack(context, "#random", f"{e.summary} at {e.dt}")
        notify_macos(e.summary, f"{e.summary} at {e.dt}")
