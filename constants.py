import os
from typing import Final
import datetime
import getpass

from environs import Env

env = Env()
env.read_env(recurse=False)

USERNAME: Final = getpass.getuser()

DEBUG: Final = env.bool("DEBUG", False)

BASE_DATA_PATH = os.path.join(os.path.expanduser("~"), ".yew.d", USERNAME, "cal")
EVENTS_FILENAME = "events.json"
EVENTS_DATA_PATH: Final = os.path.join(BASE_DATA_PATH, EVENTS_FILENAME)

CURRENT_TZ: Final = (
    datetime.datetime.now(datetime.timezone(datetime.timedelta(0))).astimezone().tzinfo
)
DEFAULT_TZ_NAME: Final = CURRENT_TZ.tzname(datetime.datetime.now())

MY_EMAIL_ADDRESS: Final = env.str("MY_EMAIL_ADDRESS")
MY_MOBILE: Final = env.str("MY_MOBILE")

MG_API_KEY: Final = env.str("MG_API_KEY")
MG_API_URL = env.str("MG_API_URL")
MG_FROM = env.str("MG_FROM")

SLACK_TOKEN: Final = env.str("SLACK_TOKEN")
SLACK_API_URL = env.str("SLACK_API_URL", "https://slack.com/api")

AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY")
BUCKET = env.str("BUCKET")

TWILIO_ACCOUNT_SID = env.str("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = env.str("TWILIO_AUTH_TOKEN")
TWILIO_ORIGIN_NUMBER = env.str("TWILIO_ORIGIN_NUMBER")
