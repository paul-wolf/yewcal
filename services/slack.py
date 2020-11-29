import json

import requests


from constants import SLACK_TOKEN

SLACK_API_URL = "https://slack.com/api/"

slack_icon_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTuGqps7ZafuzUsViFGIremEL2a3NR0KO0s0RTCMXmzmREJd5m4MA&s"


def post_message_to_slack(channel, text, blocks=None):
    return requests.post(
        "https://slack.com/api/chat.postMessage",
        {
            "token": SLACK_TOKEN,
            "channel": channel,
            "text": text,
            "icon_url": None,
            "username": "paul.wolf",
            "blocks": json.dumps(blocks) if blocks else None,
        },
    ).json()
