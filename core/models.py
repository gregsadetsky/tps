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

    player1 = models.ForeignKey(
        "CallSession", on_delete=models.PROTECT, related_name="player1"
    )
    player2 = models.ForeignKey(
        "CallSession", on_delete=models.PROTECT, related_name="player2"
    )
    player_1_move = models.CharField(max_length=255, null=True, blank=True)
    player_2_move = models.CharField(max_length=255, null=True, blank=True)

    player1_recording_url = models.CharField(max_length=255, null=True, blank=True)
    player2_recording_url = models.CharField(max_length=255, null=True, blank=True)

    STATUS_ENUM = [
        ("unknown", "unknown"),
        ("tie", "tie"),
        ("won", "won"),
    ]
    status = models.CharField(max_length=255, choices=STATUS_ENUM, default="unknown")
    winner = models.ForeignKey(
        "CallSession", on_delete=models.PROTECT, null=True, blank=True
    )

    def get_recording_url_for_other_player(self, player):
        if player == self.player1:
            return self.player2_recording_url
        elif player == self.player2:
            return self.player1_recording_url
        else:
            raise Exception("invalid player")

    def store_recording_url_for_this_player(self, player, recording_url):
        if player == self.player1:
            self.player1_recording_url = recording_url
        elif player == self.player2:
            self.player2_recording_url = recording_url
        else:
            raise Exception("invalid player")
        self.save()

    def get_move_for_this_and_other_player(self, player):
        # return tuple of this player, and other player's move
        if player == self.player1:
            return self.player_1_move, self.player_2_move
        elif player == self.player2:
            return self.player_2_move, self.player_1_move

    def has_other_player_played(self, player):
        if player == self.player1:
            return bool(self.player_2_move)
        elif player == self.player2:
            return bool(self.player_1_move)
        else:
            raise Exception("invalid player")

    def set_move_for_player(self, player, move):
        if player == self.player1:
            self.player_1_move = move
        elif player == self.player2:
            self.player_2_move = move
        else:
            raise Exception("invalid player")
        self.save()


class CallSession(models.Model):
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

    def get_current_round(self):
        return (
            Round.objects.filter(Q(player1=self) | Q(player2=self))
            .order_by("-created")
            .first()
        )

    def __str__(self):
        return self.call_sid


class TwilioLog(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    view_function = models.CharField(max_length=255)
    payload = models.JSONField()
