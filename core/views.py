from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from core.models import Caller


def index(request):
    return render(request, "core/index.html")


@csrf_exempt
def twilio_webhook(request):
    caller, _ = Caller.objects.get_or_create(phone_number=request.POST["From"])

    call_status = request.POST["CallStatus"]

    if call_status == "ringing":
        caller.state = "ingame"
        caller.save()
    elif call_status == "completed":
        caller.state = "hungup"
        caller.save()

    return HttpResponse(
        f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
              <Say>{caller.state}</Say>
            </Response>""".encode(
            "utf-8"
        )
    )
