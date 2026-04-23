import sys
import uuid
from datetime import datetime

import anthropic
from rich.console import Console

from config import (
    ANTHROPIC_API_KEY, CHROMA_PATH, MAX_TOKENS,
    MEMORY_SEARCH_RESULTS, MODEL, RECENT_HISTORY_TURNS, VAULT_PATH,
)
from memory.vault import ObsidianVault
from memory.vector import VectorMemory
from agent.tools import TOOL_DEFINITIONS, ToolExecutor, push_status, push_idle

console = Console(stderr=True)

_GREEN = "\033[1;32m"
_RESET = "\033[0m"

_SYSTEM = """\
You are Shiba, an intelligent personal AI assistant running directly on this Linux machine (Ubuntu 24.04, user: shiba). \
You have full access to the filesystem and can execute code and shell commands after user approval.

## How you operate
- **Understand intent first**: Go beyond the literal request. Read the user's underlying goal from the conversation history and context. Ask when genuinely unsure.
- **Use memory proactively**: At the start of a new topic, call `search_memory` to pull in relevant past context. Don't wait to be asked.
- **Persist what matters**: Save user preferences, project decisions, recurring needs, and key facts to the Obsidian vault.
- **Propose before acting**: For `write_file` and `execute_command`, briefly describe your plan first. The approval dialog appears automatically.
- **Be concise**: Match response length to the question. Avoid filler.

## Browser tools — NO approval needed, NO commentary
Browser tools (`browser_navigate`, `browser_click`, `browser_type`, `browser_search_youtube`, etc.) \
run instantly through the Firefox extension. Do NOT call `execute_command` for browser actions. \
Do NOT ask for approval. Do NOT announce what you are about to do. Just call the tool and report the result.

## execute_command — approval required
Only use `execute_command` for genuine shell operations (installs, builds, scripts). \
Never use it to trigger browser actions or WebSocket operations.

## Memory systems
- **Long-term — Obsidian Vault** (`~/Documents/Shiba-Vault`): Markdown notes in Daily Notes, Topics, Projects. Survives across sessions.
- **Short-term — Vector search**: Every conversation turn is indexed semantically. Use `search_memory` to recall relevant past exchanges.

## Tools available
`read_file` · `write_file` · `list_files` · `execute_command` · `search_memory` · `save_to_vault` · `read_vault` · `search_vault`
Browser: `browser_navigate` · `browser_search_youtube` · `browser_search_google` · `browser_click` · `browser_type` · `browser_press` · `browser_get_text` · `browser_evaluate` · `browser_scroll` · `browser_screenshot` · `browser_wait` · `browser_current_url`

## Session
Date: {date}   Session ID: {sid}

{user_preferences}## Context from recent sessions
{context}
"""

_USER_PREFS_BLOCK = """\
## User Preferences
{prefs}

"""


class ShibaAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.session_id = str(uuid.uuid4())[:8]
        self.history: list[dict] = []
        self.turn = 0

        console.print("[dim]Initialising memory...[/dim]", highlight=False)
        self.memory = VectorMemory(CHROMA_PATH)
        self.vault = ObsidianVault(VAULT_PATH)
        self.tools = ToolExecutor(self.memory, self.vault)

        console.print(
            f"[dim]Session [bold]{self.session_id}[/bold]  |  "
            f"{self.memory.count()} memories indexed  |  "
            f"Vault → {VAULT_PATH}[/dim]",
            highlight=False,
        )

    # ── System prompt ────────────────────────────────────────────────────────

    def _system(self) -> str:
        # Load recent daily notes for session context
        notes = self.vault.get_recent_daily_notes(2)
        parts = []
        for n in notes:
            snippet = n["content"][:700]
            parts.append(f"**{n['date']}**\n{snippet}")
        context = "\n\n".join(parts) if parts else "No previous session notes yet."

        # Load user preferences note if it exists
        prefs_note = self.vault.read_note("User Preferences")
        if prefs_note:
            user_preferences = _USER_PREFS_BLOCK.format(prefs=prefs_note.strip())
        else:
            user_preferences = ""

        return _SYSTEM.format(
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            sid=self.session_id,
            context=context,
            user_preferences=user_preferences,
        )

    # ── Chat ─────────────────────────────────────────────────────────────────

    def chat(self, user_input: str) -> str:
        """Process user input, stream response to stdout, and return full response text."""
        self.turn += 1
        self.history.append({"role": "user", "content": user_input})
        self.memory.add_turn("user", user_input, self.session_id)

        system = self._system()
        max_hist = RECENT_HISTORY_TURNS * 2
        messages = self.history[-max_hist:] if len(self.history) > max_hist else self.history[:]

        final_response = ""

        while True:
            # Signal to phone: Shiba is speaking / thinking
            push_status("speaking", "Speaking")
            text, final = self._stream(system, messages)

            if final.stop_reason != "tool_use":
                push_idle()
                response = "".join(
                    b.text for b in final.content if hasattr(b, "text")
                )
                if response.strip():
                    self.history.append({"role": "assistant", "content": response})
                    self.memory.add_turn("assistant", response, self.session_id)
                    final_response = response
                break

            # Build assistant content list (text + tool_use blocks)
            asst: list[dict] = []
            for b in final.content:
                if b.type == "text":
                    asst.append({"type": "text", "text": b.text})
                elif b.type == "tool_use":
                    asst.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
            messages.append({"role": "assistant", "content": asst})

            # Execute each tool — push_status("working", ...) is called inside ToolExecutor.execute()
            results: list[dict] = []
            for b in final.content:
                if b.type != "tool_use":
                    continue
                console.print(f"\n[dim]  ↳ tool: {b.name}[/dim]", highlight=False)
                out = self.tools.execute(b.name, b.input)
                if b.name not in ("write_file", "execute_command") and len(out) < 500:
                    console.print(f"[dim]{out}[/dim]", highlight=False)
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})

            messages.append({"role": "user", "content": results})

            # New Shiba label before next streaming response
            print()
            sys.stdout.write(f"{_GREEN}Shiba:{_RESET} ")
            sys.stdout.flush()

        return final_response

    def _stream(self, system: str, messages: list) -> tuple[str, anthropic.types.Message]:
        with self.client.messages.stream(
            model=MODEL,
            system=system,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            max_tokens=MAX_TOKENS,
        ) as stream:
            parts: list[str] = []
            for text in stream.text_stream:
                sys.stdout.write(text)
                sys.stdout.flush()
                parts.append(text)
            return "".join(parts), stream.get_final_message()

    # ── Session persistence ──────────────────────────────────────────────────

    def save_session(self) -> None:
        if not self.history:
            return
        lines = [f"## Session {self.session_id} — {datetime.now().strftime('%H:%M')}\n"]
        for msg in self.history[-40:]:
            role = "**You**" if msg["role"] == "user" else "**Shiba**"
            body = msg["content"]
            if isinstance(body, str):
                snippet = body[:400] + ("..." if len(body) > 400 else "")
                lines.append(f"{role}: {snippet}\n")
        self.vault.save_daily_note(self.session_id, "\n".join(lines))
        console.print("[dim]Session saved to vault.[/dim]", highlight=False)

    def clear_history(self) -> None:
        self.history.clear()
        self.turn = 0
