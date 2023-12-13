import hashlib

from django.urls import resolve

from core.models import CallerPerson, CallSession


def add_call_session_to_request(get_response):
    # One-time configuration and initialization.
    def middleware(request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        resolver_match = resolve(request.path_info)

        request.call_session = None
        if request.method == "POST" and request.POST.get("CallSid"):
            call_session, _ = CallSession.objects.get_or_create(
                call_sid=request.POST["CallSid"],
            )
            request.call_session = call_session

            # we are (mostly always) given the CallSid, but not always
            # given the From. update the person object when we can
            if request.POST.get("From"):
                caller_person, _ = CallerPerson.objects.get_or_create(
                    phone_number_sha1=hashlib.sha1(
                        request.POST["From"].encode("utf-8")
                    ).hexdigest()
                )
                call_session.caller_person = caller_person
                call_session.save()
            else:
                # we know that the recording callback gets the Sid but not a From (just because)
                if resolver_match.view_name != "twilio_handle_recording":
                    raise Exception("ERRRRR Received CallSid but no From...!!!")

        if request.POST.get("CallSid"):
            assert (
                request.call_session is not None
            ), "caught a None request.call_session!!!"
            print('request.POST.get("From")', request.POST.get("From"))

            # fully refresh the session from the db
            request.call_session = CallSession.objects.get(
                call_sid=request.POST["CallSid"],
            )

        response = get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    return middleware
