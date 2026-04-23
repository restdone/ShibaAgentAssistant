"""Speech-to-text using local faster-whisper. English-only filter applied after detection."""
import math
import numpy as np
import sounddevice as sd
from scipy.signal import resample_poly
from faster_whisper import WhisperModel

# Record at the device's native rate, then resample down to 16kHz for Whisper
WHISPER_RATE = 16000  # Whisper requires 16kHz
CHANNELS = 1

# Detect device's native sample rate at import time
_device_info = sd.query_devices(kind="input")
RECORD_RATE = int(_device_info["default_samplerate"])  # e.g. 44100

_model = None


def _get_model():
    global _model
    if _model is None:
        print("⏳ Loading Whisper model (first time only)...")
        _model = WhisperModel("small", device="cpu", compute_type="int8")
        print("✅ Whisper model loaded.")
    return _model


def _resample(audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
    """High-quality polyphase resample using scipy."""
    if from_rate == to_rate:
        return audio
    gcd = math.gcd(from_rate, to_rate)
    up = to_rate // gcd
    down = from_rate // gcd
    return resample_poly(audio, up, down).astype("float32")


def record_audio(stop_event) -> np.ndarray:
    """Record audio from mic until stop_event is set. Returns numpy array at WHISPER_RATE."""
    frames = []

    def callback(indata, frame_count, time_info, status):
        if status:
            print(f"[stt] stream status: {status}", flush=True)
        frames.append(indata.copy())

    with sd.InputStream(
        samplerate=RECORD_RATE,
        channels=CHANNELS,
        dtype="float32",
        callback=callback,
    ):
        stop_event.wait()  # Block until Enter is pressed again

    if not frames:
        return np.zeros((0,), dtype="float32")

    audio = np.concatenate(frames, axis=0).flatten()

    # Resample from device rate (e.g. 44100) → Whisper rate (16000)
    if RECORD_RATE != WHISPER_RATE:
        print(f"[stt] Resampling {RECORD_RATE}Hz → {WHISPER_RATE}Hz ({len(audio)} samples)", flush=True)
        audio = _resample(audio, RECORD_RATE, WHISPER_RATE)

    return audio


# Languages Whisper considers English
_ENGLISH_CODES = {"en"}


def transcribe(audio: np.ndarray) -> str:
    """Transcribe audio using faster-whisper.
    
    Returns the transcript if the detected language is English,
    otherwise silently drops the input and returns an empty string.
    """
    min_samples = WHISPER_RATE * 0.5  # at least 0.5 seconds of audio
    if len(audio) < min_samples:
        print(f"[stt] Audio too short ({len(audio)} samples), skipping.", flush=True)
        return ""

    # Debug: check audio amplitude to see if mic actually picked up sound
    peak = float(np.max(np.abs(audio)))
    print(f"[stt] Audio peak amplitude: {peak:.4f} ({len(audio)} samples @ {WHISPER_RATE}Hz)", flush=True)
    if peak < 0.005:
        print("[stt] ⚠️  Audio is nearly silent — check mic volume/permissions.", flush=True)
        return ""

    model = _get_model()

    segments, info = model.transcribe(
        audio,
        beam_size=5,
        language=None,           # Auto-detect so we can check the language
        task="transcribe",
        vad_filter=False,        # Disabled — was too aggressively filtering out speech
        condition_on_previous_text=False,
    )

    detected_lang = info.language
    lang_prob     = info.language_probability

    print(f"[stt] Detected language: {detected_lang} (confidence: {lang_prob:.2f})", flush=True)

    # ── English-only filter ──────────────────────────────────────────────────
    if detected_lang not in _ENGLISH_CODES:
        print(
            f"[stt] Non-English input detected ({detected_lang}), dropping — not sending to server.",
            flush=True,
        )
        return ""
    # ────────────────────────────────────────────────────────────────────────

    # Materialise the lazy generator fully before joining
    segment_list = list(segments)
    print(f"[stt] Segments: {len(segment_list)}", flush=True)

    transcript = " ".join(seg.text for seg in segment_list).strip()
    if transcript:
        print(f"[stt] Transcript: {transcript}", flush=True)
    else:
        print("[stt] ⚠️  Empty transcript returned by Whisper.", flush=True)

    return transcript
