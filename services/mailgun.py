import requests


from constants import MG_API_KEY, MG_API_URL, MG_FROM

def send_email(to_addresses, subject, body, from_address=None):
    from_address = from_address if from_address else MG_FROM
    return requests.post(
        "https://api.mailgun.net/v3/mg.yew.io/messages",
        auth=("api", MG_API_KEY),
        data={"from": from_address,
              "to": [to_addresses],
              "subject": subject,
              "text": body})


