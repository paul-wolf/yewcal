from twilio.rest import Client


def send_sms(context, msg):
    """Send sms."""

    client = Client(context["TWILIO_ACCOUNT_SID"], context["TWILIO_AUTH_TOKEN"])

    message = client.messages.create(
        to=context["MY_MOBILE"], from_=context["TWILIO_ORIGIN_NUMBER"], body=msg
    )

    print(message.sid)
