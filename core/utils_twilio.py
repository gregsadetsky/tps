import os

from django.conf import settings
from twilio.rest import Client

account_sid = settings.TWILIO_ACCOUNT_SID
auth_token = settings.TWILIO_AUTH_TOKEN
client = Client(account_sid, auth_token)


def interrupt_call_and_redirect_them_to_url(call_sid, redirect_url):
    client.calls(call_sid).update(method="POST", url=redirect_url)
