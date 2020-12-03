from twilio.rest import Client

import constants


def send_sms(msg):
    """Send sms."""

    client = Client(constants.TWILIO_ACCOUNT_SID, constants.TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        to=constants.MY_MOBILE, from_=constants.TWILIO_ORIGIN_NUMBER, body=msg
    )

    print(message.sid)
