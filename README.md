# Django project tps

Hi! This is the Django source for tps.

## TODO

If you followed the [minimalish django starter](https://github.com/gregsadetsky/minimalish-django-starter) instructions, you still have a couple of steps to go to make a thing that lives on the internet.

next:

- create a new postgres database locally ([look here for more](#you-need-a-postgresql-database))
- duplicate `.env.example` to `.env` and fill it out
- run `python manage.py migrate`
- start the server with `python manage.py runserver`
- do good work

finally:

- create a new repo (on github -- [go here](https://github.com/new))
- git add/commit/push all of your code to this new repo
- go to [render.com](https://render.com/), go to "[Blueprints](https://dashboard.render.com/blueprints)" and click the "New Blueprint Instance" button. assuming that your github account is connected to your render account, connect your new repo with the new blueprint
  - set the `ALLOWED_HOSTS` value to the domain name you want to use and/or the `.onrender.com` sub-domain (see below). comma separate domains if you have multiple.
  - it can be confusing to do the previous step because you won't know which .onrender.com domain you'll be given when setting up the blueprint... uh... I guess you can write some domain in ALLOWED_HOSTS like example.com, do the render blueprint deployment, then see which domain you actually got, and then edit the ALLOWED_HOSTS value to the right .onrender.com domain... sorry, this is not perfect! TODO make it better.
- ok phew, you should be live!!!
- delete this whole TODO section in this readme and anything else you want to delete; you could keep the little [powered by minimalish django starter](https://github.com/gregsadetsky/minimalish-django-starter) note at the bottom? but don't fret.

# Development basics

## You need a PostgreSQL database

For the project to work in development mode, you'll need to have PostgreSQL running, and PostgreSQL will need to have a database named `tps` inside it. If you're on mac, I suggest [Postgres.app](https://postgresapp.com/) to run postgres locally and [Postico](https://eggerapps.at/postico2/) to view & change stuff in the database.

## Getting started the first time

To get started, navigate to the directory where this code lives. If you're downloading this code fresh, you'll need to run these commands:

```
python3 -m venv venv
pip install -r requirements.txt
```

## Getting started every time

If you've done that before, or if you just did the [minimalish-django-starter setup](https://github.com/gregsadetsky/minimalish-django-starter), you can skip those two lines and just run

```
source venv/bin/activate
python manage.py runserver
```

If you get hollered at to run some other command like `python manage.py migrate` hit Ctrl-C to stop the server, do that and then run `python manage.py runserver` again, no worries.

-----

[powered by minimalish django starter](https://github.com/gregsadetsky/minimalish-django-starter) # tps
