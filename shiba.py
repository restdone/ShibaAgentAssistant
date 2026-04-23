#!/usr/bin/env python3
"""Shiba — personal AI assistant. Run: python shiba.py [--voice | --vad] [--mobile]"""
import readline  # noqa: F401 — activates arrow-key history and line editing for input()
import re
import signal
import subprocess
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel

console = Console()

_CYAN = "\033[1;36m"
_GREEN = "\033[1;32m"
_RESET = "\033[0m"

# ── New-session trigger detection ────────────────────────────────────────────

_NEW_SESSION_PATTERNS = [
    r"\bnew\s+(conversation|session|chat|convo)\b",
    r"\bstart\s+(over|fresh|again|a\s+new)\b",
    r"\bfresh\s+start\b",
    r"\breset\s+(the\s+)?(conversation|session|chat)\b",
    r"\bclear\s+(the\s+)?(conversation|session|chat)\b",
]

_NEW_SESSION_RE = re.compile(
    "|".join(_NEW_SESSION_PATTERNS),
    re.IGNORECASE,
)


def _is_new_session_request(text: str) -> bool:
    return bool(_NEW_SESSION_RE.search(text))


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    # Parse args
    parser = argparse.ArgumentParser(description="Shiba — personal AI assistant")
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Enable voice mode with push-to-talk (press Enter to start/stop)",
    )
    parser.add_argument(
        "--vad",
        action="store_true",
        help="Enable voice mode with automatic voice activity detection (no button needed)",
    )
    parser.add_argument(
        "--mobile",
        action="store_true",
        help="Enable mobile approval mode — send write/execute approvals to the Android app",
    )
    args = parser.parse_args()

    # --vad implies voice output (TTS) as well
    voice_mode = args.voice or args.vad

    from config import ANTHROPIC_API_KEY, VAULT_PATH

    if not ANTHROPIC_API_KEY:
        console.print(
            "[bold red]No API key found.[/bold red] "
            "Run: [cyan]export ANTHROPIC_API_KEY='sk-ant-...'[/cyan]"
        )
        sys.exit(1)

    # ── Start file server in the background ──────────────────────────────────
    _file_server_dir = Path(__file__).parent
    _file_server_proc = subprocess.Popen(
        [sys.executable, str(_file_server_dir / "file_server.py")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    console.print("[dim]File server started on port 1990.[/dim]")

    # ── Enable mobile approval before the agent (and tools) load ─────────────
    if args.mobile:
        from agent.tools import enable_mobile_approval
        enable_mobile_approval()

    # ── Mode label for the startup banner ─────────────────────────────────────
    if args.vad:
        mode_label = "🎤  VAD mode  ·  Speak naturally, pause to send"
    elif args.voice:
        mode_label = "🎙️  Voice mode  ·  Press [ENTER] to speak"
    else:
        mode_label = "⌨️  Text mode"

    approval_label = "📱  Mobile approval" if args.mobile else "⌨️  Terminal approval"

    console.print(Panel.fit(
        f"[bold cyan]Shiba[/bold cyan]  —  your personal AI on this machine\n"
        f"[dim]Vault: {VAULT_PATH}[/dim]\n"
        f"[dim]{mode_label}  ·  {approval_label}  ·  'exit' to quit  ·  'clear' to reset  ·  Ctrl+C to save & exit[/dim]",
        border_style="cyan",
    ))

    from agent.core import ShibaAgent
    agent = ShibaAgent()

    # Load voice modules only if needed
    if voice_mode:
        from voice.tts import speak

        if args.vad:
            from voice.voice_activity import listen_once_vad as listen_once
        else:
            from voice.push_to_talk import listen_once

    def _shutdown(sig=None, frame=None) -> None:
        print()
        agent.save_session()
        _file_server_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)

    while True:
        try:
            if voice_mode:
                # Voice input (either VAD or push-to-talk)
                user_input = listen_once()
                if not user_input:
                    console.print("[dim]Didn't catch that, try again.[/dim]")
                    continue
                print(f"\n{_CYAN}You:{_RESET} {user_input}")
            else:
                # Text input
                user_input = input(f"\n{_CYAN}You:{_RESET} ").strip()

        except EOFError:
            _shutdown()

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "bye"):
            _shutdown()

        if user_input.lower() == "clear":
            agent.clear_history()
            console.print("[dim]Conversation history cleared.[/dim]")
            continue

        # ── New session request ──────────────────────────────────────────────
        if _is_new_session_request(user_input):
            agent.save_session()
            agent = ShibaAgent()
            msg = "Starting fresh. New session ready."
            console.print(f"\n[dim]{msg}[/dim]")
            if voice_mode:
                speak(msg)
            continue

        sys.stdout.write(f"\n{_GREEN}Shiba:{_RESET} ")
        sys.stdout.flush()

        response = agent.chat(user_input)
        print()

        if voice_mode and response:
            speak(response)


if __name__ == "__main__":
    main()
