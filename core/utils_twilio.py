import os
import time

from django.conf import settings
from twilio.rest import Client

account_sid = settings.TWILIO_ACCOUNT_SID
auth_token = settings.TWILIO_AUTH_TOKEN
client = Client(account_sid, auth_token)


# returns whether interrupt was successful
def try_interrupting_call_and_redirect_them_to_url(call_sid, redirect_url):
    try:
        client.calls(call_sid).update(method="POST", url=redirect_url)
        return True
    except:
        return False


def is_the_call_still_around(call_sid):
    try:
        call = client.calls(call_sid).fetch()
        return call.status != "completed"
    except:
        return False
