import urllib

import requests


def send_email(context, to_addresses, subject, body, from_address=None):
    from_address = from_address or context["MG_FROM"]
    return requests.post(
        urllib.parse.urljoin(context["MG_API_URL"], "messages"),
        auth=("api", context["MG_API_KEY"]),
        data={
            "from": from_address,
            "to": [to_addresses],
            "subject": subject,
            "text": body,
        },
    )
