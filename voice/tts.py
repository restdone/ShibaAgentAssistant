"""Text-to-speech using edge-tts (no API key needed). Plays audio back through speakers."""
import asyncio
import os
import tempfile

import edge_tts
import sounddevice as sd
import soundfile as sf

# Voice options (edge-tts): en-US-AriaNeural, en-US-GuyNeural, zh-HK-HiuMaanNeural (Cantonese)
TTS_VOICE = "en-US-AriaNeural"


def speak(text: str) -> None:
    """Convert text to speech and play it out loud."""
    if not text.strip():
        return

    asyncio.run(_speak_async(text))


async def _speak_async(text: str) -> None:
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        communicate = edge_tts.Communicate(text, TTS_VOICE)
        await communicate.save(tmp_path)

        data, samplerate = sf.read(tmp_path)
        sd.play(data, samplerate)
        sd.wait()
    finally:
        os.unlink(tmp_path)
