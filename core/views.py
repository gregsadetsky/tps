from django.conf import settings
from django.http import Http404, HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from core.models import Caller, Round, TwilioLog

from .utils_speechrec import transcribe_rps_from_url
from .utils_twilio import interrupt_call_and_redirect_them_to_url

HOLD_MUSIC = "http://com.twilio.music.guitars.s3.amazonaws.com/Pitx_-_Long_Winter.mp3"


def _get_user_from_request(request):
    caller, _ = Caller.objects.get_or_create(
        current_call_sid=request.POST["CallSid"],
    )
    return caller


@csrf_exempt
def twilio_handle_round_result(request):
    user = _get_user_from_request(request)

    current_round = user.get_current_round()
    assert current_round is not None
    played_moves = current_round.get_move_for_this_and_other_player(user)

    verbal_output = ""
    if current_round.status == "tie":
        verbal_output = "it was a tie! amazing"
    else:
        if current_round.winner == user:
            verbal_output = "you won! amazing"
        else:
            verbal_output = "you lost! not amazing"

    return HttpResponse(
        f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say>you played {played_moves[0]}</Say>
        <Say>they played {played_moves[1]}</Say>
        <Say>{verbal_output}</Say>
    </Response>""".encode(
            "utf-8"
        )
    )


def compute_round_winner(round):
    if round.last_player_1_move == round.last_player_2_move:
        round.status = "tie"
        round.save()
        return

    RPS = ["rock", "paper", "scissors"]
    player1_rps = RPS.index(round.last_player_1_move)
    player2_rps = RPS.index(round.last_player_2_move)

    if player2_rps == (player1_rps + 1) % 3:
        round.status = "won"
        round.winner = round.player2
        round.save()
        return
    elif player1_rps == (player2_rps + 1) % 3:
        round.status = "won"
        round.winner = round.player1
        round.save()
        return
    else:
        raise Exception("please never happen")


@csrf_exempt
def twilio_handle_recording(request):
    user = _get_user_from_request(request)

    recording_url = request.POST["RecordingUrl"]
    transcription = transcribe_rps_from_url(recording_url)

    current_round = user.get_current_round()
    assert current_round is not None

    if transcription == "rock":
        current_round.set_move_for_player(user, "rock")
    elif transcription == "paper":
        current_round.set_move_for_player(user, "paper")
    elif transcription == "scissors":
        current_round.set_move_for_player(user, "scissors")
    else:
        # we didn't get that, ask the user to record again
        user.state = "rerecording"
        user.save()

        # interrupt this user's hold and send them back to twilio_handle_game
        interrupt_call_and_redirect_them_to_url(
            call_sid=user.current_call_sid,
            redirect_url=f'{settings.SERVER_URL}{reverse("twilio_handle_game")}',
        )
        return HttpResponse(b"ok")

    if current_round.has_other_player_played(user):
        # 1. determine who won
        compute_round_winner(current_round)

        # both players have played -- interrupt both users as we know who won
        interrupt_call_and_redirect_them_to_url(
            call_sid=current_round.player1.current_call_sid,
            redirect_url=f'{settings.SERVER_URL}{reverse("twilio_handle_round_result")}',
        )
        interrupt_call_and_redirect_them_to_url(
            call_sid=current_round.player2.current_call_sid,
            redirect_url=f'{settings.SERVER_URL}{reverse("twilio_handle_round_result")}',
        )

    return HttpResponse(b"ok")


@csrf_exempt
def twilio_handle_game(request):
    user = _get_user_from_request(request)

    if user.state == "started_game":
        user.state = "waiting_for_transcript"
        user.save()

        return HttpResponse(
            f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>please play</Say>
                <Record timeout="2" playBeep="true" recordingStatusCallback="{reverse('twilio_handle_recording')}" />
            </Response>
        """.encode(
                "utf-8"
            )
        )
    elif user.state == "rerecording":
        user.state = "waiting_for_transcript"
        user.save()

        return HttpResponse(
            f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>we didn't quite hear that, please say rock papers or scissors</Say>
                <Record timeout="2" playBeep="true" recordingStatusCallback="{reverse('twilio_handle_recording')}" />
            </Response>
        """.encode(
                "utf-8"
            )
        )
    elif user.state == "waiting_for_transcript":
        # play music forever
        return HttpResponse(
            f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Play loop="100">{HOLD_MUSIC}</Play>
            </Response>
        """.encode(
                "utf-8"
            )
        )

    # otherwise should never happen
    raise Exception()


def handle_ringing(request):
    user = _get_user_from_request(request)

    # we are looking to see if another user is waiting
    # to play -- if so, we'll connect the two users
    # otherwise, put this user in waiting state
    # and ... say/play music..??

    found_other_waiting_user = (
        Caller.objects.exclude(id=user.id)
        .filter(state="waiting_for_other_player")
        .order_by("?")
        .first()
    )

    if found_other_waiting_user:
        user.state = "started_game"
        user.save()

        found_other_waiting_user.state = "started_game"
        found_other_waiting_user.save()

        # create round
        Round.objects.create(player1=user, player2=found_other_waiting_user)

        interrupt_call_and_redirect_them_to_url(
            call_sid=found_other_waiting_user.current_call_sid,
            redirect_url=f'{settings.SERVER_URL}{reverse("twilio_handle_game")}',
        )

        return HttpResponse(
            f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>you are now about to play with another user</Say>
                <Redirect method="POST">{reverse("twilio_handle_game")}</Redirect>
            </Response>""".encode(
                "utf-8"
            )
        )

    # otherwise, put this user in waiting state
    user.state = "waiting_for_other_player"
    user.save()

    return HttpResponse(
        f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>you are now in waiting state</Say>
            <Play loop="100">{HOLD_MUSIC}</Play>
        </Response>""".encode(
            "utf-8"
        )
    )


def handle_hangup(request):
    user = _get_user_from_request(request)

    user.state = "hungup"
    user.save()

    return HttpResponse(b"ok")


@csrf_exempt
def twilio_webhook(request):
    TwilioLog.objects.create(post_blob=request.POST)

    assert request.POST.get("CallStatus")
    call_status = request.POST["CallStatus"]

    if call_status == "ringing":
        # the very initial time that the user calls in
        return handle_ringing(request)
    elif call_status == "completed":
        return handle_hangup(request)

    return HttpResponse(b"ok")
