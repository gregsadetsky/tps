import random

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from core.models import CallSession, Round

from .utils_logging import log_twilio_payload
from .utils_server_url import get_server_url
from .utils_speechrec import transcribe_rps_from_url
from .utils_twilio import (
    is_the_call_still_around,
    try_interrupting_call_and_redirect_them_to_url,
)
from .utils_wins_losses import generate_welcome_say_twiml_for_call_session

HOLD_MUSIC = "http://com.twilio.music.guitars.s3.amazonaws.com/Pitx_-_Long_Winter.mp3"
AUTHORS = [
    '<a href="https://eieio.games/">eieio</a>',
    '<a href="https://greg.technology/">greg technology</a>',
]

UNINTERRUPTIBLE_STATES = {
    "listening_to_results",
}


def index(request):
    shuffled_authors = AUTHORS.copy()
    random.shuffle(shuffled_authors)
    return render(request, "core/index.html", {"authors": shuffled_authors})


@csrf_exempt
@log_twilio_payload
def twilio_handle_round_result(request):
    current_round = request.call_session.get_latest_round()
    assert current_round is not None

    request.call_session.set_state("listening_to_results")

    current_player_move = current_round.get_move_for_this_player(request.call_session)

    verbal_output = ""
    if current_round.status == "tie":
        verbal_output = "it was a tie! good job."
    else:
        if current_round.winner_session == request.call_session:
            verbal_output = "you won! you're amazing."
        else:
            verbal_output = "you lost! I'm sorry."

    other_player_recording_url = current_round.get_recording_url_for_other_player(
        request.call_session
    )

    return HttpResponse(
        f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say>you played {current_player_move}</Say>
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
    else:
        raise Exception("please never happen")
    round.save()


@csrf_exempt
@log_twilio_payload
def twilio_handle_recording(request):
    recording_url = request.POST["RecordingUrl"]
    transcription = transcribe_rps_from_url(recording_url)

    current_round = request.call_session.get_latest_round()
    assert current_round is not None

    current_round.store_recording_url_for_this_player(
        request.call_session, recording_url
    )

    if transcription in {"rock", "paper", "scissors"}:
        current_round.set_move_for_player(request.call_session, transcription)
    else:
        # we didn't get that, ask the user to record again

        # FIXME the other person may have hung up at this point, so DON'T transition to rerecording, which mixes up things
        # FIXME the other person may have hung up at this point, so DON'T transition to rerecording, which mixes up things
        # FIXME the other person may have hung up at this point, so DON'T transition to rerecording, which mixes up things
        # FIXME the other person may have hung up at this point, so DON'T transition to rerecording, which mixes up things
        request.call_session.set_state("rerecording")

        # interrupt this user's hold and send them back to twilio_handle_game
        try_interrupting_call_and_redirect_them_to_url(
            call_sid=request.call_session.call_sid,
            redirect_url=f'{get_server_url()}{reverse("twilio_handle_game")}',
        )
        return HttpResponse(b"ok")

    if current_round.has_other_player_played(request.call_session):
        # 1. determine who won
        compute_and_save_round_winner(current_round)

        # both players have played -- interrupt both users as we know who won

        try_interrupting_call_and_redirect_them_to_url(
            call_sid=current_round.player1_session.call_sid,
            redirect_url=f'{get_server_url()}{reverse("twilio_handle_round_result")}',
        )

        try_interrupting_call_and_redirect_them_to_url(
            call_sid=current_round.player2_session.call_sid,
            redirect_url=f'{get_server_url()}{reverse("twilio_handle_round_result")}',
        )

    return HttpResponse(b"ok")


@csrf_exempt
@log_twilio_payload
def twilio_handle_game(request):
    if request.call_session.state == "started_game":
        request.call_session.set_state("waiting_for_transcript")

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
        request.call_session.set_state("waiting_for_transcript")

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


@csrf_exempt
def put_user_in_waiting_queue(request):
    # we are looking to see if another user is waiting
    # to play -- if so, we'll connect the two users
    # otherwise, put this user in waiting state
    # and ... say/play music..??

    other_waiting_call_session = (
        CallSession.objects.exclude(id=request.call_session.id)
        .filter(state="waiting_for_other_player")
        .order_by("?")
        .first()
    )

    if not other_waiting_call_session:
        request.call_session.set_state("waiting_for_other_player")

        return HttpResponse(
            f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>please wait for another player</Say>
                <Play loop="100">{HOLD_MUSIC}</Play>
            </Response>""".encode(
                "utf-8"
            )
        )

    # no actually there was another call!! let's go
    interrupt_was_successful = try_interrupting_call_and_redirect_them_to_url(
        call_sid=other_waiting_call_session.call_sid,
        redirect_url=f'{get_server_url()}{reverse("twilio_handle_game")}',
    )
    if not interrupt_was_successful:
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
    request.call_session.set_state("started_game")
    other_waiting_call_session.set_state("started_game")

    # create round
    Round.objects.create(
        player1_session=request.call_session,
        player2_session=other_waiting_call_session,
    )

    return HttpResponse(
        f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Redirect method="POST">{reverse("twilio_handle_game")}</Redirect>
        </Response>""".encode(
            "utf-8"
        )
    )


# called by `twilio_webhook` i.e. the dispatcher of ringing+hangup webhook calls
def handle_ringing(request):
    # otherwise, put this user in waiting state
    request.call_session.set_state("being_welcomed")

    return HttpResponse(
        f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            {generate_welcome_say_twiml_for_call_session(request.call_session)}
            <Redirect method="POST">{reverse("put_user_in_waiting_queue")}</Redirect>
        </Response>""".encode(
            "utf-8"
        )
    )


@csrf_exempt
def announce_bad_news(request):
    return HttpResponse(
        b"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say>Sorry... the other player hung up, goodbye.</Say>
        <Hangup/>
    </Response>"""
    )


# called by `twilio_webhook` i.e. the dispatcher of ringing+hangup webhook calls
def handle_hangup(request):
    request.call_session.set_state("hungup")

    # the player hung up, great, BUT
    # did they leave someone hanging?? that would be major not cool.
    # if so, interrupt that person and tell them that the other person hung up.

    latest_round = request.call_session.get_latest_round()
    if latest_round is not None:
        other_session = latest_round.get_the_other_players_session(request.call_session)

        if other_session.state not in UNINTERRUPTIBLE_STATES:
            # try to interrupt the other session and let them know that the other person hung up
            try_interrupting_call_and_redirect_them_to_url(
                call_sid=other_session.call_sid,
                redirect_url=f'{get_server_url()}{reverse("announce_bad_news")}',
            )

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
