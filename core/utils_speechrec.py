import tempfile

import requests
from django.conf import settings
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_KEY)


def transcribe_rps_from_url(url):
    print("transcribe_speech_from_url url", url)

    response = requests.get(url)

    # with tempfile.TemporaryFile(suffix=".wav") as fp:
    with open("/tmp/audio.wav", "wb") as fp:
        fp.write(response.content)

    with open("/tmp/audio.wav", "rb") as fp:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=fp,
            prompt="ROCK, PAPER, SCISSORS",
        )

    return transcript.text
