from django.urls import path
from django.views.generic import TemplateView

from core.views import (
    announce_bad_news,
    index,
    put_user_in_waiting_queue,
    twilio_handle_game,
    twilio_handle_recording,
    twilio_handle_round_result,
    twilio_webhook,
)

urlpatterns = [
    path("", index, name="index"),
    path(
        "twilio_handle_recording",
        twilio_handle_recording,
        name="twilio_handle_recording",
    ),
    path("twilio_handle_game", twilio_handle_game, name="twilio_handle_game"),
    path(
        "twilio_handle_round_result",
        twilio_handle_round_result,
        name="twilio_handle_round_result",
    ),
    path("twilio_webhook", twilio_webhook, name="twilio_webhook"),
    path("announce_bad_news", announce_bad_news, name="announce_bad_news"),
    path(
        "put_user_in_waiting_queue",
        put_user_in_waiting_queue,
        name="put_user_in_waiting_queue",
    ),
]
