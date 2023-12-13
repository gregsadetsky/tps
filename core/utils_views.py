from functools import wraps

from django.http import HttpResponse


def ping_pong_twilio_redirect_hack(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        # does the GET arg hack contain nothing? i.e. ping
        # THEN redirect to hack=pong
        # if hack=pong, then let through
        if request.GET.get("hack") != "pong":
            return HttpResponse(
                f"""<?xml version="1.0" encoding="UTF-8"?>
                    <Response>
                        <Redirect method="POST">{request.path_info}?hack=pong</Redirect>
                    </Response>""".encode(
                    "utf-8"
                )
            )
        return function(request, *args, **kwargs)

    return wrap
