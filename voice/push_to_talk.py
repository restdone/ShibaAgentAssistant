"""Push-to-talk controller. Press Enter to start recording, Enter again to stop."""
import threading

from voice.stt import record_audio, transcribe


def listen_once() -> str:
    """
    Block until user presses Enter, records audio, then presses Enter again to stop.
    Returns transcript string, or empty string if nothing was captured.
    """
    print("\n🎙️  Press [ENTER] to start speaking...", flush=True)
    input()  # Wait for first Enter

    stop_event = threading.Event()

    print("🔴 Recording... (press [ENTER] to send)", flush=True)

    # Run recording in a background thread so we can wait for Enter simultaneously
    audio_holder = [None]

    def record():
        audio_holder[0] = record_audio(stop_event)

    record_thread = threading.Thread(target=record, daemon=True)
    record_thread.start()

    input()  # Wait for second Enter to stop recording
    stop_event.set()
    record_thread.join()

    print("⏳ Transcribing...", flush=True)
    transcript = transcribe(audio_holder[0])

    return transcript
