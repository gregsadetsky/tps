import os

import requests
from django.conf import settings


# on prod, return the setting.SERVER_URL
# on dev, get the dynamic server address from ngrok
def get_server_url():
    if os.environ.get("DJANGO_SETTINGS_MODULE") == "tps.settings.prod":
        # on prod, return the setting.SERVER_URL
        return settings.SERVER_URL
    else:
        r = requests.get("http://localhost:4040/api/tunnels")
        return r.json()["tunnels"][0]["public_url"]
