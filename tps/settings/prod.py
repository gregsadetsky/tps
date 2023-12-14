from .base import *

# default logging doesn't log to console with DEBUG=False
# see https://github.com/django/django/blob/main/django/utils/log.py
# override i.e. always log to console
LOGGING["handlers"]["console"] = {
    "class": "logging.StreamHandler",
}

# conn_max_age makes sense for prod! AND DOES NOT FOR DEV!
DATABASES = {
    "default": dj_database_url.config(
        conn_max_age=600,
    )
}
