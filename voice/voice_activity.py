"""Voice Activity Detection (VAD) listener.

Continuously monitors the microphone and automatically starts recording
when speech is detected, then stops after a period of silence.

Usage:
    from voice.voice_activity import listen_once_vad
    transcript = listen_once_vad()
"""

import numpy as np
import sounddevice as sd

from voice.stt import transcribe, RECORD_RATE, WHISPER_RATE, _resample

# --- Tunable parameters ---
CHUNK_DURATION   = 0.03          # seconds per analysis chunk (30ms)
CHUNK_SAMPLES    = int(RECORD_RATE * CHUNK_DURATION)

SILENCE_THRESHOLD = 0.01         # RMS below this = silence
SPEECH_THRESHOLD  = 0.015        # RMS above this = speech

PRE_SPEECH_CHUNKS  = 10          # keep this many chunks before speech onset (padding)
MIN_SPEECH_CHUNKS  = 5           # minimum chunks to count as real speech (~150ms)
SILENCE_CHUNKS     = 40          # chunks of silence before we decide speech ended (~1.2s)


def _rms(chunk: np.ndarray) -> float:
    return float(np.sqrt(np.mean(chunk ** 2)))


def listen_once_vad() -> str:
    """
    Block until speech is detected, record until silence, return transcript.
    Prints a minimal status line so the user knows what's happening.
    """
    print("\n👂  Listening... (speak naturally, pause to send)", flush=True)

    ring_buffer = []          # circular pre-speech buffer
    recording   = []          # actual captured audio
    speech_chunks  = 0
    silence_chunks = 0
    in_speech = False

    with sd.InputStream(
        samplerate=RECORD_RATE,
        channels=1,
        dtype="float32",
        blocksize=CHUNK_SAMPLES,
    ) as stream:
        while True:
            chunk, _ = stream.read(CHUNK_SAMPLES)
            chunk = chunk.flatten()
            level = _rms(chunk)

            if not in_speech:
                # Keep a rolling pre-speech buffer
                ring_buffer.append(chunk)
                if len(ring_buffer) > PRE_SPEECH_CHUNKS:
                    ring_buffer.pop(0)

                if level >= SPEECH_THRESHOLD:
                    speech_chunks += 1
                    if speech_chunks >= 2:          # need 2 consecutive loud chunks
                        in_speech = True
                        print("🔴 Recording...", flush=True)
                        recording.extend(ring_buffer)
                        ring_buffer.clear()
                        speech_chunks = 0
                else:
                    speech_chunks = 0

            else:
                recording.append(chunk)

                if level < SILENCE_THRESHOLD:
                    silence_chunks += 1
                else:
                    silence_chunks = 0

                if silence_chunks >= SILENCE_CHUNKS:
                    print("⏳ Transcribing...", flush=True)
                    break

    if not recording:
        return ""

    audio = np.concatenate(recording, axis=0).astype("float32")

    # Resample to Whisper's required 16kHz
    if RECORD_RATE != WHISPER_RATE:
        audio = _resample(audio, RECORD_RATE, WHISPER_RATE)

    return transcribe(audio)
