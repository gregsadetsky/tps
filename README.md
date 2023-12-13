# Talk Paper Scissors

## how to install

- roughly follow instructions [from here](https://github.com/gregsadetsky/minimalish-django-starter#lets-do-it-immediately), ping greg...

## how to dev

- `source venv/bin/activate`
- `python manage.py runserver`
- `ngrok http 8000`
- then! go to twilio console (for the current dev number [go here](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming/PN0535e666c2e5cec6f8cbb11114bb1674/configure)) and set:
  - the dev number's voice's webhook URL
  - AND "call status changes" URL
  - to `https://...THE-NGROK-DOMAIN..../twilio_webhook`
