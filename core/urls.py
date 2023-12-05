from django.urls import path

from core.views import index, twilio_webhook

urlpatterns = [
    path(
        "",
        index,
        name="index",
    ),
    path("twilio_webhook", twilio_webhook, name="twilio_webhook"),
]
