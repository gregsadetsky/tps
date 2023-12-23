# Talk Paper Scissors

## basic dev considerations/requirements

- this is a python/django backend project. you'll need to have python 3.10ish (3.11 is fine), install Django & other requirements. and also have ngrok installed and working.
- you will also! need access to 1) a twilio phone number & api key 2) an openai account/api key (to do the speech recognition)

## how to install

- roughly follow instructions [from here](https://github.com/gregsadetsky/minimalish-django-starter#lets-do-it-immediately)
- fill out the missing values in the `.env` file (copied over from `.env.example`) i.e. the twilio & openai API keys
- ping us in the issues here if you have trouble with any of this

## how to dev

- `source venv/bin/activate`
- `python manage.py runserver`
- `ngrok http 8000`
- then! go to twilio console for the phone number you're using and set:
  - the dev number's voice's webhook URL...
  - AND "call status changes" URL...
  - ... to `https://...THE-NGROK-DOMAIN..../twilio_webhook`
