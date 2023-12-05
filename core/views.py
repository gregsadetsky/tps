from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from core.models import Caller

from .utils_speechrec import transcribe_rps_from_url


def index(request):
    return render(request, "core/index.html")


@csrf_exempt
def twilio_webhook(request):
    print(request.POST)

    caller, _ = Caller.objects.get_or_create(
        current_call_sid=request.POST["CallSid"],
    )

    if request.POST.get("RecordingStatus") == "completed":
        recording_url = request.POST["RecordingUrl"]
        transcription = transcribe_rps_from_url(recording_url)
        print("transcription", transcription)
        return HttpResponse(b"ok")

    call_status = request.POST["CallStatus"]
    print("call_status", call_status)

    if call_status == "ringing":
        caller.state = "ingame"
        caller.save()

        print("returning record")

        return HttpResponse(
            f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>please play</Say>
                <Record timeout="2" playBeep="true" recordingStatusCallback="{reverse('twilio_webhook')}" />
                <Say>recording done</Say>
            </Response>""".encode(
                "utf-8"
            )
        )

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
