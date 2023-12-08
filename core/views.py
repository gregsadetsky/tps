import random

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from core.models import CallSession, Round

from .utils_logging import log_twilio_payload
from .utils_server_url import get_server_url
from .utils_speechrec import transcribe_rps_from_url
from .utils_twilio import interrupt_call_and_redirect_them_to_url

HOLD_MUSIC = "http://com.twilio.music.guitars.s3.amazonaws.com/Pitx_-_Long_Winter.mp3"
AUTHORS = [
    '<a href="https://eieio.games/">Nolen Royalty</a>',
    '<a href="https://greg.technology/">Greg Technology</a>',
]


def index(request):
    shuffled_authors = AUTHORS.copy()
    random.shuffle(shuffled_authors)
    return render(request, "core/index.html", {"authors": shuffled_authors})


@csrf_exempt
@log_twilio_payload
def twilio_handle_round_result(request):
    current_round = request.call_session.get_current_round()
    assert current_round is not None
    played_moves = current_round.get_move_for_this_and_other_player(
        request.call_session
    )

    verbal_output = ""
    if current_round.status == "tie":
        verbal_output = "it was a tie! good job."
    else:
        if current_round.winner_session == request.call_session:
            verbal_output = "you won! youu're amazing."
        else:
            verbal_output = "you lost! I'm sorry."

    other_player_recording_url = current_round.get_recording_url_for_other_player(
        request.call_session
    )

    return HttpResponse(
        f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say>you played {played_moves[0]}</Say>
        <Say>they played</Say>
        <Play>{other_player_recording_url}</Play>
        <Say>{verbal_output}</Say>
    </Response>""".encode(
            "utf-8"
        )
    )


def compute_and_save_round_winner(round):
    if round.player1_move == round.player2_move:
        round.status = "tie"
        round.save()
        return

    RPS = ["rock", "paper", "scissors"]
    player1_rps = RPS.index(round.player1_move)
    player2_rps = RPS.index(round.player2_move)

    round.status = "won"
    if player2_rps == (player1_rps + 1) % 3:
        round.winner_session = round.player2_session
    elif player1_rps == (player2_rps + 1) % 3:
        round.winner_session = round.player1_session
        return
    else:
        raise Exception("please never happen")
    round.save()


@csrf_exempt
@log_twilio_payload
def twilio_handle_recording(request):
    recording_url = request.POST["RecordingUrl"]
    transcription = transcribe_rps_from_url(recording_url)

    current_round = request.call_session.get_current_round()
    assert current_round is not None

    current_round.store_recording_url_for_this_player(
        request.call_session, recording_url
    )

    if transcription == "rock":
        current_round.set_move_for_player(request.call_session, "rock")
    elif transcription == "paper":
        current_round.set_move_for_player(request.call_session, "paper")
    elif transcription == "scissors":
        current_round.set_move_for_player(request.call_session, "scissors")
    else:
        # we didn't get that, ask the user to record again
        request.call_session.state = "rerecording"
        request.call_session.save()

        # interrupt this user's hold and send them back to twilio_handle_game
        try:
            interrupt_call_and_redirect_them_to_url(
                call_sid=request.call_session.call_sid,
                redirect_url=f'{get_server_url()}{reverse("twilio_handle_game")}',
            )
        except:
            # the user hung up while being asked to re-record. too bad.
            pass
        return HttpResponse(b"ok")

    if current_round.has_other_player_played(request.call_session):
        # 1. determine who won
        compute_and_save_round_winner(current_round)

        # both players have played -- interrupt both users as we know who won

        try:
            interrupt_call_and_redirect_them_to_url(
                call_sid=current_round.player1_session.call_sid,
                redirect_url=f'{get_server_url()}{reverse("twilio_handle_round_result")}',
            )
        except:
            # the user hung up. it doesn't matter, they already won/lost.
            pass

        try:
            interrupt_call_and_redirect_them_to_url(
                call_sid=current_round.player2_session.call_sid,
                redirect_url=f'{get_server_url()}{reverse("twilio_handle_round_result")}',
            )
        except:
            # the user hung up. it doesn't matter, they already won/lost.
            pass

    return HttpResponse(b"ok")


@csrf_exempt
@log_twilio_payload
def twilio_handle_game(request):
    if request.call_session.state == "started_game":
        request.call_session.state = "waiting_for_transcript"
        request.call_session.save()

        return HttpResponse(
            f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>please say rock, papers or scissors</Say>
                <Record timeout="2" maxLength="3" playBeep="true" recordingStatusCallback="{reverse('twilio_handle_recording')}" />
            </Response>
        """.encode(
                "utf-8"
            )
        )
    elif request.call_session.state == "rerecording":
        request.call_session.state = "waiting_for_transcript"
        request.call_session.save()

        return HttpResponse(
            f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>we didn't quite hear that, please say rock, papers or scissors</Say>
                <Record timeout="2" maxLength="3" playBeep="true" recordingStatusCallback="{reverse('twilio_handle_recording')}" />
            </Response>
        """.encode(
                "utf-8"
            )
        )
    elif request.call_session.state == "waiting_for_transcript":
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


# called by `twilio_webhook` i.e. the dispatcher of ringing+hangup webhook calls
def handle_ringing(request):
    # we are looking to see if another user is waiting
    # to play -- if so, we'll connect the two users
    # otherwise, put this user in waiting state
    # and ... say/play music..??

    found_other_waiting_user = (
        CallSession.objects.exclude(id=request.call_session.id)
        .filter(state="waiting_for_other_player")
        .order_by("?")
        .first()
    )

    if found_other_waiting_user:
        try:
            interrupt_call_and_redirect_them_to_url(
                call_sid=found_other_waiting_user.call_sid,
                redirect_url=f'{get_server_url()}{reverse("twilio_handle_game")}',
            )
        except:
            # interrupting the other caller failed, assume
            # that this because they hung up. abort.
            return HttpResponse(
                b"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>the other player hung up, goodbye</Say>
                <Hangup/>
            </Response>"""
            )

        # we assume that we interrupted the other player successfully, continue

        request.call_session.state = "started_game"
        request.call_session.save()

        found_other_waiting_user.state = "started_game"
        found_other_waiting_user.save()

        # create round
        Round.objects.create(
            player1_session=request.call_session, player2=found_other_waiting_user
        )

        return HttpResponse(
            f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Redirect method="POST">{reverse("twilio_handle_game")}</Redirect>
            </Response>""".encode(
                "utf-8"
            )
        )

    # otherwise, put this user in waiting state
    request.call_session.state = "waiting_for_other_player"
    request.call_session.save()

    return HttpResponse(
        f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>please wait for another player</Say>
            <Play loop="100">{HOLD_MUSIC}</Play>
        </Response>""".encode(
            "utf-8"
        )
    )


# called by `twilio_webhook` i.e. the dispatcher of ringing+hangup webhook calls
def handle_hangup(request):
    request.call_session.state = "hungup"
    request.call_session.save()

    return HttpResponse(b"ok")


@csrf_exempt
@log_twilio_payload
def twilio_webhook(request):
    assert request.POST.get("CallStatus")
    call_status = request.POST["CallStatus"]

    if call_status == "ringing":
        # the very initial time that the user calls in
        return handle_ringing(request)
    elif call_status == "completed":
        return handle_hangup(request)

    return HttpResponse(b"ok")
