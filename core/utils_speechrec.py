import re
import tempfile
from pathlib import Path

import requests
from django.conf import settings
from openai import OpenAI

from core.models import TranscriptionLogs

# FIXME test and try retries??????
# FIXME test and try retries??????
# FIXME test and try retries??????
# FIXME test and try retries??????
# FIXME test and try retries??????
# FIXME test and try retries??????
# FIXME test and try retries??????
# FIXME test and try retries??????
# FIXME test and try retries??????
# FIXME test and try retries??????
# FIXME test and try retries??????
# FIXME test and try retries??????
# FIXME test and try retries??????
client = OpenAI(api_key=settings.OPENAI_KEY, timeout=10)


def transcribe_rps_from_url(url):
    response = requests.get(url)

    with tempfile.TemporaryDirectory() as tmpdirname:
        audio_file_path = Path(tmpdirname) / "audio.wav"

        with open(audio_file_path, "wb") as fp:
            fp.write(response.content)

        with open(audio_file_path, "rb") as fp:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=fp,
                prompt="ROCK, PAPER, SCISSORS",
            )

    TranscriptionLogs.objects.create(transcript=transcript.text)
    return re.sub(r"\W+", "", transcript.text.lower().strip())
