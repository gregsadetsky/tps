import urllib.parse
from contextlib import contextmanager
from functools import wraps
from xml.sax.saxutils import escape

from django.db.transaction import atomic
from django.http import HttpResponse

from .models import ThreadSafe


def ping_pong_twilio_redirect_hack(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        # does the GET arg hack contain nothing? i.e. ping
        # THEN redirect to hack=pong
        # if hack=pong, then let through
        if request.GET.get("hack") != "pong":
            current_args = request.GET.copy()
            current_args["hack"] = "pong"
            # xml escape the url encoded string!! & needs to be &amp;
            serialized_get_args = escape(urllib.parse.urlencode(current_args))

            return HttpResponse(
                f"""<?xml version="1.0" encoding="UTF-8"?>
                    <Response>
                        <Redirect method="POST">{request.path_info}?{serialized_get_args}</Redirect>
                    </Response>""".encode(
                    "utf-8"
                )
            )
        return function(request, *args, **kwargs)

    return wrap


@contextmanager
def lock(key):
    pk = ThreadSafe.objects.get_or_create(key=key)[0].pk
    try:
        objs = ThreadSafe.objects.filter(pk=pk).select_for_update()
        with atomic():
            list(objs)
            yield None
    finally:
        pass
