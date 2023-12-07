from django.urls import path

from core.views import (
    twilio_handle_game,
    twilio_handle_recording,
    twilio_handle_round_result,
    twilio_webhook,
)

urlpatterns = [
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
]
