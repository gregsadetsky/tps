from core.models import CallSession


def add_call_session_to_request(get_response):
    # One-time configuration and initialization.
    def middleware(request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        request.call_session = None
        if request.method == "POST" and request.POST.get("CallSid"):
            call_session, _ = CallSession.objects.get_or_create(
                call_sid=request.POST["CallSid"],
            )
            request.call_session = call_session
        response = get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    return middleware
