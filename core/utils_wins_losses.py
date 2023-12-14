from django.db.models import Q


def generate_welcome_say_twiml_for_call_session(call_session):
    GENERIC_WELCOME_MSG = "<Say>Welcome to Talk Paper Scissors!</Say>"
    # if call_session does not have reference to caller_person, just say welcome
    if not call_session.caller_person:
        return GENERIC_WELCOME_MSG

    wins_losses_and_ties = get_wins_losses_and_ties_for_caller_person_obj(
        caller_person_obj=call_session.caller_person
    )

    # if wins losses and ties are 0, just say welcome
    if (
        wins_losses_and_ties["wins"] == 0
        and wins_losses_and_ties["losses"] == 0
        and wins_losses_and_ties["ties"] == 0
    ):
        return GENERIC_WELCOME_MSG

    # otherwise, say welcome and wins losses and ties
    wins_str = "wins" if wins_losses_and_ties["wins"] != 1 else "win"
    losses_str = "losses" if wins_losses_and_ties["losses"] != 1 else "loss"
    ties_str = "ties" if wins_losses_and_ties["ties"] != 1 else "tie"
    return f"""<Say>Welcome to Talk Paper Scissors! You have {wins_losses_and_ties["wins"]} {wins_str}, {wins_losses_and_ties["losses"]} {losses_str}, and {wins_losses_and_ties["ties"]} {ties_str}.</Say>"""


def get_wins_losses_and_ties_for_call_session(call_session):
    # since this function is used in models, avoid circular import
    from core.models import Round

    wins = 0
    losses = 0
    ties = 0

    # get all rounds where this call_session was a player,
    # and the round was won, and the winner was set
    for round_obj in Round.objects.filter(
        (Q(player1_session=call_session) | Q(player2_session=call_session)),
        (Q(status="won") | Q(status="tie")),
    ):
        if round_obj.status == "won" and round_obj.winner_session:
            if round_obj.winner_session == call_session:
                wins += 1
            else:
                losses += 1
        elif round_obj.status == "tie":
            ties += 1

    return {"wins": wins, "losses": losses, "ties": ties}


def get_wins_losses_and_ties_for_caller_person_obj(caller_person_obj):
    # since this function is used in models, avoid circular import
    from core.models import Round

    wins = 0
    losses = 0
    ties = 0

    # get all rounds where this caller_person_obj was a player,
    # and the round was won, and the winner was set
    for round_obj in Round.objects.filter(
        (
            Q(player1_session__caller_person=caller_person_obj)
            | Q(player2_session__caller_person=caller_person_obj)
        ),
        (Q(status="won") | Q(status="tie")),
    ):
        if round_obj.status == "won" and round_obj.winner_session:
            if round_obj.winner_session.caller_person == caller_person_obj:
                wins += 1
            else:
                losses += 1
        elif round_obj.status == "tie":
            ties += 1

    return {"wins": wins, "losses": losses, "ties": ties}
