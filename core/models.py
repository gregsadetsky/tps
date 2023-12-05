from django.contrib.auth.models import AbstractUser
from django.db import models


# https://docs.djangoproject.com/en/4.2/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project
class User(AbstractUser):
    pass


class Game(models.Model):
    player1 = models.ForeignKey(
        "Caller", on_delete=models.PROTECT, related_name="player1"
    )
    player2 = models.ForeignKey(
        "Caller", on_delete=models.PROTECT, related_name="player2"
    )


class Caller(models.Model):
    phone_number = models.CharField(max_length=255)

    CALLER_STATE = [("hungup", "hungup"), ("ingame", "ingame")]
    state = models.CharField(max_length=255, choices=CALLER_STATE)
    game = models.ForeignKey(Game, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return self.phone_number
