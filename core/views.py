import datetime
import random

from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from core.models import CallSession, Round

from .utils_server_url import get_server_url
from .utils_speechrec import transcribe_rps_from_url
from .utils_twilio import (
    is_the_call_still_around,
    try_interrupting_call_and_redirect_them_to_url,
)
from .utils_views import lock, ping_pong_twilio_redirect_hack
from .utils_wins_losses import (
    generate_welcome_say_twiml_for_call_session,
    get_wins_losses_and_ties_for_call_session,
)

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
def end_of_game_handler(request):
    # get all of the rounds for this caller session
    # compute the score
    # and say goodbye

    wins_losses_and_ties = get_wins_losses_and_ties_for_call_session(
        request.call_session
    )
    total_score = wins_losses_and_ties["wins"] - wins_losses_and_ties["losses"]

    final_result_str = ""
    if total_score == 0:
        final_result_str = "tied"
    elif total_score > 0:
        final_result_str = "won"
    else:
        final_result_str = "lost"

    return HttpResponse(
        f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>Your final score is: {total_score}</Say>
            <Say>You {final_result_str}</Say>
            <Say>Goodbye!</Say>
            <Hangup/>
        </Response>""".encode(
            "utf-8"
        )
    )


@csrf_exempt
@ping_pong_twilio_redirect_hack
def new_round_handler(request):
    most_recent_round = request.call_session.get_latest_round()
    next_round_number = int(request.GET["next_round_number"])

    if next_round_number == 3:
        return end_of_game_handler(request)

    # check if the other player is still around - otherwise bail
    if not is_the_call_still_around(
        most_recent_round.get_the_other_players_session(request.call_session).call_sid
    ):
        return HttpResponse(
            f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>the other player hung up, goodbye</Say>
                <Hangup/>
            </Response>""".encode(
                "utf-8"
            )
        )

    # using get_or_create as it will only create a single object
    # thanks to primary keys
    Round.objects.get_or_create(
        player1_session=most_recent_round.player1_session,
        player2_session=most_recent_round.player2_session,
        round_number=next_round_number,
    )

    request.call_session.set_state("started_round")

    return HttpResponse(
        f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>Round {next_round_number+1}!</Say>
            <Redirect method="POST">{reverse("twilio_handle_game")}</Redirect>
        </Response>""".encode(
            "utf-8"
        )
    )


@csrf_exempt
def twilio_handle_round_result(request):
    current_round = request.call_session.get_latest_round()
    assert current_round is not None

    request.call_session.set_state("listening_to_results")

    current_player_move = current_round.get_move_for_this_player(request.call_session)

    verbal_output = ""
    if current_round.status == "tie":
        verbal_output = "the round was a tie!"
    else:
        if current_round.winner_session == request.call_session:
            verbal_output = "you won the round!"
        else:
            verbal_output = "you lost the round!"

    other_player_recording_url = current_round.get_recording_url_for_other_player(
        request.call_session
    )

    next_round_number = current_round.round_number + 1

    return HttpResponse(
        f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say>you played {current_player_move}</Say>
        <Say>they played</Say>
        <Play>{other_player_recording_url}</Play>
        <Say>{verbal_output}</Say>
        <Redirect method="POST">{reverse("new_round_handler")}?next_round_number={next_round_number}</Redirect>
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
def twilio_handle_recording(request):
    recording_url = request.POST["RecordingUrl"]
    try:
        transcription = transcribe_rps_from_url(recording_url)
    except:
        transcription = "error"

    # this value will be fetched within a lock
    other_player_played = False
    is_transcription_valid = transcription in {"rock", "paper", "scissors"}

    # yes, this will line is duplicated below.
    current_round = request.call_session.get_latest_round()
    with lock(f"round_{current_round.id}"):
        # this, this line is duplicate above.
        current_round = request.call_session.get_latest_round()
        assert current_round is not None

        if is_transcription_valid:
            current_round.set_move_for_player(request.call_session, transcription)
        other_player_played = current_round.has_other_player_played(
            request.call_session
        )

        current_round.store_recording_url_for_this_player(
            request.call_session, recording_url
        )

    if is_transcription_valid:
        # reset incorrect transcripts
        request.call_session.number_of_incorrect_transcripts = 0
        request.call_session.save()

    if not is_transcription_valid:
        # we didn't get that, ask the user to record again
        request.call_session.set_state("rerecording")

        # is the other call still around?? it might not be;
        # in that case, stop this recording handler from doing anything else
        if not is_the_call_still_around(
            current_round.get_the_other_players_session(request.call_session).call_sid
        ):
            return HttpResponse(b"ok")

        # interrupt this user's hold and send them back to twilio_handle_game
        try_interrupting_call_and_redirect_them_to_url(
            call_sid=request.call_session.call_sid,
            redirect_url=f'{get_server_url()}{reverse("twilio_handle_game")}',
        )
        return HttpResponse(b"ok")

    if other_player_played:
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
def twilio_handle_game(request):
    if request.call_session.state == "started_round":
        request.call_session.set_state("waiting_for_transcript")

        return HttpResponse(
            f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>please say rock, paper or scissors</Say>
                <Record timeout="2" maxLength="3" playBeep="true" recordingStatusCallback="{reverse('twilio_handle_recording')}" />
            </Response>
        """.encode(
                "utf-8"
            )
        )
    elif request.call_session.state == "rerecording":
        if request.call_session.number_of_incorrect_transcripts == 4:
            # assume that something is not working - either the player
            # is messing with us/the other player, or their line just doesn't work.
            # hang up this user and that will also lead the other player to be hung up
            # in the hungup handler
            return HttpResponse(
                b"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>we're sorry, we could not understand you, goodbye</Say>
                <Hangup/>
            </Response>"""
            )

        request.call_session.number_of_incorrect_transcripts += 1
        request.call_session.save()

        request.call_session.set_state("waiting_for_transcript")

        return HttpResponse(
            f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>we didn't quite hear that, please say rock, paper or scissors</Say>
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
    raise Exception(f"unexpected state!!! >>> {request.call_session.state}")


@csrf_exempt
@ping_pong_twilio_redirect_hack
def put_user_in_waiting_queue(request):
    # we are looking to see if another user is waiting
    # to play -- if so, we'll connect the two users
    # otherwise, put this user in waiting state
    # and ... say/play music..??

    with lock("put_user_in_waiting_queue"):
        other_waiting_call_session = (
            CallSession.objects.exclude(id=request.call_session.id)
            .filter(state="waiting_for_other_player")
            .order_by("?")
            .first()
        )

        if not other_waiting_call_session:
            request.call_session.set_state("waiting_for_other_player")

            recent_call_session_message = ""
            nmb_recent_call_sessions = (
                CallSession.objects.filter(
                    # get all sessions more recent than 5 minutes ago
                    created__gte=(
                        datetime.datetime.now(datetime.timezone.utc)
                        - datetime.timedelta(minutes=5)
                    ),
                ).count()
                - 1
            )
            if nmb_recent_call_sessions > 50:
                recent_call_session_message = "\n<Say>more than 50 people have played in the last 5 minutes.</Say>"
            elif nmb_recent_call_sessions > 0:
                recent_call_session_message = f"\n<Say>{nmb_recent_call_sessions} people have played in the last 5 minutes.</Say>"

            return HttpResponse(
                f"""<?xml version="1.0" encoding="UTF-8"?>
                <Response>
                    <Say>please wait for another player</Say>{recent_call_session_message}
                    <Play loop="1">{HOLD_MUSIC}</Play>
                    <Say>we're sorry, we could not find another player</Say>
                    <Hangup/>
                </Response>""".encode(
                    "utf-8"
                )
            )

    # no actually there was another call!! let's go
    request.call_session.set_state("started_round")
    other_waiting_call_session.set_state("started_round")

    # create round
    Round.objects.create(
        player1_session=request.call_session,
        player2_session=other_waiting_call_session,
        round_number=0,
    )

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
def twilio_webhook(request):
    assert request.POST.get("CallStatus")
    call_status = request.POST["CallStatus"]

    if call_status == "ringing":
        # the very initial time that the user calls in
        return handle_ringing(request)
    elif call_status == "completed":
        return handle_hangup(request)

    return HttpResponse(b"ok")


def dashboard(request):
    def get_count_of_states(query):
        all_counts_by_state = query.values("state").annotate(count=Count("state"))
        state_count_dict = {x["state"]: x["count"] for x in all_counts_by_state}
        # alpha order the keys and return as list
        out = [["TOTAL", sum(state_count_dict.values())]]
        out += sorted(state_count_dict.items())
        return out

    total_call_session_states = get_count_of_states(CallSession.objects.all())

    last_30m_call_sessions = get_count_of_states(
        CallSession.objects.filter(
            created__gte=(
                datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(minutes=30)
            )
        )
    )

    last_2m_call_sessions = get_count_of_states(
        CallSession.objects.filter(
            created__gte=(
                datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(minutes=2)
            )
        )
    )

    return render(
        request,
        "core/dashboard.html",
        {
            "total_call_session_states": total_call_session_states,
            "last_30m_call_sessions": last_30m_call_sessions,
            "last_2m_call_sessions": last_2m_call_sessions,
        },
    )
