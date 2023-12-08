from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


# https://docs.djangoproject.com/en/4.2/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project
class User(AbstractUser):
    pass


class TranscriptionLogs(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    transcript = models.TextField()


class Round(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    player1_session = models.ForeignKey(
        "CallSession", on_delete=models.PROTECT, related_name="player1_session"
    )
    player2_session = models.ForeignKey(
        "CallSession", on_delete=models.PROTECT, related_name="player2_session"
    )

    player1_move = models.CharField(max_length=255, null=True, blank=True)
    player2_move = models.CharField(max_length=255, null=True, blank=True)

    player1_recording_url = models.CharField(max_length=255, null=True, blank=True)
    player2_recording_url = models.CharField(max_length=255, null=True, blank=True)

    STATUS_ENUM = [
        ("unknown", "unknown"),
        ("tie", "tie"),
        ("won", "won"),
    ]
    status = models.CharField(max_length=255, choices=STATUS_ENUM, default="unknown")
    winner_session = models.ForeignKey(
        "CallSession", on_delete=models.PROTECT, null=True, blank=True
    )

    def get_recording_url_for_other_player(self, player_session):
        if player_session == self.player1_session:
            return self.player2_recording_url
        elif player_session == self.player2_session:
            return self.player1_recording_url
        else:
            raise Exception("invalid player session")

    def store_recording_url_for_this_player(self, player_session, recording_url):
        if player_session == self.player1_session:
            self.player1_recording_url = recording_url
        elif player_session == self.player2_session:
            self.player2_recording_url = recording_url
        else:
            raise Exception("invalid player session")
        self.save()

    def get_move_for_this_player(self, player_session):
        if player_session == self.player1_session:
            return self.player1_move
        elif player_session == self.player2_session:
            return self.player2_move

    def has_other_player_played(self, player_session):
        if player_session == self.player1_session:
            return bool(self.player2_move)
        elif player_session == self.player2_session:
            return bool(self.player1_move)
        else:
            raise Exception("invalid player session")

    def set_move_for_player(self, player_session, move):
        if player_session == self.player1_session:
            self.player1_move = move
        elif player_session == self.player2_session:
            self.player2_move = move
        else:
            raise Exception("invalid player session")
        self.save()


class CallSession(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    call_sid = models.CharField(max_length=255, null=True, blank=True)

    SESSION_STATE = [
        ("hungup", "hungup"),
        ("waiting_for_other_player", "waiting_for_other_player"),
        ("started_game", "started_game"),
        ("rerecording", "rerecording"),
        ("waiting_for_transcript", "waiting_for_transcript"),
    ]
    state = models.CharField(max_length=255, choices=SESSION_STATE)

    def get_latest_round(self):
        return (
            Round.objects.filter(Q(player1_session=self) | Q(player2_session=self))
            .order_by("-created")
            .first()
        )

    def __str__(self):
        return self.call_sid


class TwilioLog(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    view_function = models.CharField(max_length=255)
    payload = models.JSONField()
