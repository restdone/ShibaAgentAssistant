import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax

console = Console()

# ── Approval mode ─────────────────────────────────────────────────────────────
_mobile_mode = False
_request_approval_fn = None
_set_status_fn = None
_clear_status_fn = None

# ── Auto-approve patterns ─────────────────────────────────────────────────────
# execute_command calls matching any of these substrings are run without prompting.
_AUTO_APPROVE_PATTERNS = [
    "ws_server.py",
    "ext_tools.py",
    "curl http://localhost:9010",
    "curl http://localhost:9009",
]

# Tools that never need approval (run silently).
_NO_APPROVAL_TOOLS = {
    "browser_navigate",
    "browser_get_text",
    "browser_click",
    "browser_type",
    "browser_press",
    "browser_screenshot",
    "browser_wait",
    "browser_current_url",
    "browser_search_youtube",
    "browser_search_google",
    "browser_close",
    "browser_evaluate",
    "browser_scroll",
    "browser_open_tab",
    "read_file",
    "list_files",
    "search_memory",
    "read_vault",
    "search_vault",
    "save_to_vault",
}


def enable_mobile_approval():
    global _mobile_mode, _request_approval_fn, _set_status_fn, _clear_status_fn
    try:
        from approval_server import request_approval, start_background, set_status, clear_status
        start_background()
        _request_approval_fn = request_approval
        _set_status_fn = set_status
        _clear_status_fn = clear_status
        _mobile_mode = True
        console.print("[bold cyan]Mobile approval mode enabled.[/bold cyan]  Waiting for phone…")
    except Exception as e:
        console.print(f"[red]Could not start mobile approval server: {e}[/red]")
        console.print("[dim]Falling back to terminal approval.[/dim]")


def push_status(state: str, message: str = ""):
    if _mobile_mode and _set_status_fn is not None:
        try:
            _set_status_fn(state, message)
        except Exception:
            pass


def push_idle():
    if _mobile_mode and _clear_status_fn is not None:
        try:
            _clear_status_fn()
        except Exception:
            pass


def _ask_approval(action_type: str, summary: str, detail: str, timeout: int = 120) -> bool:
    if _mobile_mode and _request_approval_fn is not None:
        console.print(
            f"[bold cyan]▶ Approval request sent to phone[/bold cyan]  ({action_type})\n"
            f"[dim]{summary}[/dim]"
        )
        return _request_approval_fn(action_type, summary, detail, timeout=timeout)
    return Confirm.ask(f"[yellow]Approve {action_type}?[/yellow]")


def _is_auto_approved_command(command: str) -> bool:
    return any(pat in command for pat in _AUTO_APPROVE_PATTERNS)


# ── Tool label map ────────────────────────────────────────────────────────────

_TOOL_LABELS = {
    "read_file":              "Reading a file",
    "write_file":             "Writing a file",
    "execute_command":        "Running a command",
    "search_memory":          "Searching memory",
    "save_to_vault":          "Saving to memory",
    "read_vault":             "Reading memory",
    "search_vault":           "Searching memory",
    "list_files":             "Listing files",
    "browser_navigate":       "Opening page",
    "browser_get_text":       "Reading page",
    "browser_click":          "Clicking element",
    "browser_type":           "Typing in browser",
    "browser_press":          "Pressing key",
    "browser_screenshot":     "Taking screenshot",
    "browser_wait":           "Waiting",
    "browser_current_url":    "Checking page",
    "browser_search_youtube": "Searching YouTube",
    "browser_search_google":  "Searching Google",
    "browser_evaluate":       "Running JS",
    "browser_scroll":         "Scrolling page",
    "browser_close":          "Closing browser",
    "browser_open_tab":       "Opening new tab",
}


# ── Tool definitions ──────────────────────────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": "Read the contents of any file on the filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "max_lines": {"type": "integer", "description": "Max lines to read (default 300)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": (
            "Write content to a file. Creates or overwrites. "
            "Shows a preview and asks for user approval before writing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Destination file path"},
                "content": {"type": "string", "description": "File content"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "execute_command",
        "description": (
            "Run a shell command on this machine. "
            "Shows the command and asks for user approval before executing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command"},
                "working_dir": {"type": "string", "description": "Working directory (optional)"},
                "timeout": {"type": "integer", "description": "Timeout seconds (default 60)"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "search_memory",
        "description": "Semantic search over all past conversation history. Use to recall relevant past context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "n_results": {"type": "integer", "description": "Number of results (default 5)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "save_to_vault",
        "description": (
            "Save a note to the Obsidian vault for long-term memory. "
            "Use for user preferences, project details, decisions, and important facts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Note title"},
                "content": {"type": "string", "description": "Markdown content"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for the note",
                },
                "folder": {
                    "type": "string",
                    "description": "Vault folder: Topics (default), Projects, or Daily Notes",
                },
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "read_vault",
        "description": "Read a note from the Obsidian vault by name, or list all notes if no name is given.",
        "input_schema": {
            "type": "object",
            "properties": {
                "note_name": {"type": "string", "description": "Note name (omit to list all)"},
            },
        },
    },
    {
        "name": "search_vault",
        "description": "Full-text search across all notes in the Obsidian vault.",
        "input_schema": {
            "type": "object",
            "properties": {
                "term": {"type": "string", "description": "Search term"},
            },
            "required": ["term"],
        },
    },
    {
        "name": "list_files",
        "description": "List files and directories at a path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path"},
                "pattern": {"type": "string", "description": "Glob pattern (e.g. '*.py')"},
            },
            "required": ["path"],
        },
    },
    # ── Browser tools (via Firefox extension) ─────────────────────────────────
    {
        "name": "browser_navigate",
        "description": "Navigate Firefox to a URL. No approval needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL to navigate to"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "browser_get_text",
        "description": "Get visible text content of the current Firefox tab.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "browser_click",
        "description": "Click an element in Firefox by CSS selector.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of the element to click"},
            },
            "required": ["selector"],
        },
    },
    {
        "name": "browser_type",
        "description": "Type text into an input field in Firefox by CSS selector.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of the input field"},
                "text": {"type": "string", "description": "Text to type"},
            },
            "required": ["selector", "text"],
        },
    },
    {
        "name": "browser_press",
        "description": "Press a keyboard key in the current Firefox tab (e.g. 'Enter').",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key name to press"},
            },
            "required": ["key"],
        },
    },
    {
        "name": "browser_screenshot",
        "description": "Take a screenshot of the current Firefox tab.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "browser_wait",
        "description": "Wait for a number of seconds.",
        "input_schema": {
            "type": "object",
            "properties": {
                "seconds": {"type": "number", "description": "Seconds to wait (default 2.0)"},
            },
        },
    },
    {
        "name": "browser_current_url",
        "description": "Return the current Firefox tab URL and title.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "browser_search_youtube",
        "description": (
            "Search YouTube for a query and return the top video titles and URLs. "
            "Use this to find videos, music, tutorials, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "browser_search_google",
        "description": "Search Google for a query and return results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "browser_evaluate",
        "description": "Run JavaScript in the current Firefox tab and return the result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "JavaScript code to evaluate"},
            },
            "required": ["code"],
        },
    },
    {
        "name": "browser_scroll",
        "description": "Scroll the current Firefox tab by a number of pixels.",
        "input_schema": {
            "type": "object",
            "properties": {
                "y": {"type": "integer", "description": "Pixels to scroll (default 500)"},
            },
        },
    },
    {
        "name": "browser_close",
        "description": "Close the browser session.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "browser_open_tab",
        "description": "Open a new tab in Firefox. Optionally navigate to a URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to open in the new tab (optional)"},
            },
        },
    },
]


class ToolExecutor:
    def __init__(self, vector_memory, vault):
        self.memory = vector_memory
        self.vault = vault

    def execute(self, name: str, inputs: dict) -> str:
        fn = getattr(self, f"_{name}", None)
        if fn is None:
            return f"Unknown tool: {name}"
        label = _TOOL_LABELS.get(name, "Working on it")
        push_status("working", label)
        try:
            return fn(**inputs)
        except Exception as e:
            return f"Tool error ({name}): {e}"
        finally:
            push_idle()

    # ── Core tools ────────────────────────────────────────────────────────────

    def _read_file(self, path: str, max_lines: int = 300) -> str:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"Not found: {path}"
        if p.is_dir():
            return f"Path is a directory: {path}"
        try:
            text = p.read_text(errors="replace")
            lines = text.splitlines()
            if len(lines) > max_lines:
                return "\n".join(lines[:max_lines]) + f"\n\n[... {len(lines)-max_lines} lines truncated]"
            return text
        except Exception as e:
            return f"Read error: {e}"

    def _write_file(self, path: str, content: str) -> str:
        p = Path(path).expanduser().resolve()

        summary = f"Write file: {p.name}"
        detail = (
            f"Path: {p}\n"
            f"Size: {len(content)} bytes  |  {len(content.splitlines())} lines\n\n"
            + "\n".join(content.splitlines()[:60])
            + ("\n\n[... truncated ...]" if len(content.splitlines()) > 60 else "")
        )

        print()
        console.print(f"[bold yellow]▶ Write File:[/bold yellow] {p}")
        ext = p.suffix.lstrip(".") or "text"
        preview = "\n".join(content.splitlines()[:40])
        if len(content.splitlines()) > 40:
            preview += f"\n[... {len(content.splitlines())-40} more lines ...]"
        console.print(Panel(
            Syntax(preview, ext, theme="monokai", line_numbers=True),
            title=f"[yellow]{p.name}[/yellow]",
            border_style="yellow",
        ))

        if not _ask_approval("write_file", summary, detail):
            return "Declined: write not approved."

        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Written: {p} ({len(content)} bytes)"

    def _execute_command(self, command: str, working_dir: str = None, timeout: int = 60) -> str:
        summary = command if len(command) <= 80 else command[:77] + "..."
        detail = f"Command:\n{command}"
        if working_dir:
            detail += f"\n\nWorking directory: {working_dir}"

        auto = _is_auto_approved_command(command)

        if not auto:
            print()
            console.print("[bold red]▶ Execute Command:[/bold red]")
            console.print(Panel(Syntax(command, "bash", theme="monokai"), border_style="red"))
            if working_dir:
                console.print(f"[dim]  cwd: {working_dir}[/dim]")
            if not _ask_approval("execute_command", summary, detail):
                return "Declined: execution not approved."
        else:
            console.print(f"[dim]  ↳ auto-approved: {summary}[/dim]", highlight=False)

        cwd = Path(working_dir).expanduser() if working_dir else None
        try:
            r = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=cwd,
            )
            parts = []
            if r.stdout.strip():
                parts.append(f"stdout:\n{r.stdout.rstrip()}")
            if r.stderr.strip():
                parts.append(f"stderr:\n{r.stderr.rstrip()}")
            parts.append(f"exit code: {r.returncode}")
            return "\n\n".join(parts)
        except subprocess.TimeoutExpired:
            return f"Timed out after {timeout}s"

    def _search_memory(self, query: str, n_results: int = 5) -> str:
        results = self.memory.search(query, n_results)
        if not results:
            return "No relevant memories found."
        lines = []
        for r in results:
            ts = r["timestamp"][:16] if r["timestamp"] else "?"
            lines.append(f"[{ts}] {r['role']} (score {r['score']}):\n{r['content']}")
        return "\n\n---\n\n".join(lines)

    def _save_to_vault(
        self, title: str, content: str, tags: list[str] = None, folder: str = "Topics"
    ) -> str:
        path = self.vault.save_note(title, content, tags or [], folder)
        return f"Saved: {path}"

    def _read_vault(self, note_name: str = None) -> str:
        if note_name:
            text = self.vault.read_note(note_name)
            return text if text else f"Note not found: {note_name}"
        notes = self.vault.list_notes()
        if not notes:
            return "Vault is empty."
        return "Vault notes:\n" + "\n".join(f"  {n}" for n in notes)

    def _search_vault(self, term: str) -> str:
        result = self.vault.cli_search(term)
        return result if result else f"No vault notes match: {term}"

    def _list_files(self, path: str, pattern: str = None) -> str:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"Not found: {path}"
        if not p.is_dir():
            return f"Not a directory: {path}"
        items = sorted(p.glob(pattern) if pattern else p.iterdir(),
                       key=lambda x: (x.is_file(), x.name.lower()))
        lines = [("/" if i.is_dir() else " ") + i.name for i in items[:150]]
        if len(items) > 150:
            lines.append(f"  ... and {len(items)-150} more")
        return f"{path}/\n" + "\n".join(lines) if lines else f"{path}/ (empty)"

    # ── Browser tools (Firefox extension via ext_tools.py) ────────────────────

    def _ext(self, command: str, params: dict = None) -> str:
        """Send a command to the Firefox extension via the HTTP bridge."""
        from browser_extension.ext_tools import _send
        try:
            result = _send(command, params or {})
            return str(result) if result is not None else "OK"
        except RuntimeError as e:
            return f"Browser error: {e}"

    def _browser_navigate(self, url: str) -> str:
        return self._ext("navigate", {"url": url})

    def _browser_get_text(self) -> str:
        return self._ext("get_text")

    def _browser_click(self, selector: str) -> str:
        return self._ext("click", {"selector": selector})

    def _browser_type(self, selector: str, text: str) -> str:
        return self._ext("type", {"selector": selector, "text": text})

    def _browser_press(self, key: str) -> str:
        return self._ext("evaluate", {"code": f"document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {{key: '{key}', bubbles: true}}))"})

    def _browser_screenshot(self) -> str:
        return self._ext("screenshot")

    def _browser_wait(self, seconds: float = 2.0) -> str:
        import time
        time.sleep(seconds)
        return f"Waited {seconds}s"

    def _browser_current_url(self) -> str:
        return self._ext("get_info")

    def _browser_search_youtube(self, query: str) -> str:
        import urllib.parse
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
        nav_result = self._ext("navigate", {"url": url})
        import time
        time.sleep(2)
        # Extract video titles and links via JS
        result = self._ext("evaluate", {"code": """
            (() => {
                const items = document.querySelectorAll('ytd-video-renderer, ytd-compact-video-renderer');
                const out = [];
                for (const el of Array.from(items).slice(0, 8)) {
                    const a = el.querySelector('a#video-title, a.ytd-compact-video-renderer');
                    if (a && a.href && a.textContent.trim()) {
                        out.push(a.textContent.trim() + ' | ' + a.href);
                    }
                }
                return out.join('\\n');
            })()
        """})
        if result and result.strip():
            return f"YouTube results for '{query}':\n{result}"
        return f"Navigated to YouTube search for '{query}'. {nav_result}"

    def _browser_search_google(self, query: str) -> str:
        import urllib.parse
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
        return self._ext("navigate", {"url": url})

    def _browser_evaluate(self, code: str) -> str:
        return self._ext("evaluate", {"code": code})

    def _browser_scroll(self, y: int = 500) -> str:
        return self._ext("scroll", {"y": y})

    def _browser_close(self) -> str:
        # No-op for the extension — we don't close Firefox
        return "Browser session ended (Firefox stays open)."

    def _browser_open_tab(self, url: str = None) -> str:
        params = {"url": url} if url else {}
        return self._ext("open_tab", params)
