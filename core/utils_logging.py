from core.models import TwilioLog

# view decorator for twilio handlers that takes a view function
# and will log the payload we receive on request.POST to the database


def log_twilio_payload(view_function):
    def wrapped_view(request):
        twilio_log = TwilioLog.objects.create(
            view_function=view_function.__name__,
            payload=request.POST,
        )
        return view_function(request)

    return wrapped_view
