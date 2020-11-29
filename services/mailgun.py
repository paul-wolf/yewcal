import smtplib, os


import requests
import urllib3
import certifi

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

def xxxsend_email(to, subject, message, from_address="", data_extra={}):
    """Send an email via Mailgun using the REST API."""
    from_address = from_address if from_address else MG_FROM
    data = {"from": from_address, "to": to, "subject": subject, "text": message}
    data.update(data_extra)
    print(f"Posting to mailgun: {to}")
    pool = urllib3.PoolManager(cert_reqs="CERT_REQUIRED", ca_certs=certifi.where())
    auth = f"api:{MG_API_KEY}"
    headers = urllib3.util.make_headers(basic_auth=auth)
    r = pool.request("POST", MG_API_URL, headers=headers, fields=data)
    print(r)
    return r.data
