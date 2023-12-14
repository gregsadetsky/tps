from .base import *

DEBUG = True

ALLOWED_HOSTS += [".ngrok-free.app"]

# conn_max_age makes sense for prod! AND DOES NOT FOR DEV!
DATABASES = {"default": dj_database_url.config()}
