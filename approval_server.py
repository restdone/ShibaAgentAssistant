"""
Shiba Approval Server
---------------------
Runs a lightweight Flask server on the local WiFi interface.
The Android app polls /approval/pending, shows approve/reject UI,
and posts the decision to /approval/respond.

Also exposes /vault/list and /vault/read for the Memory screen.
Also exposes /status for the live Shiba status bar in the app.

Start it with:  python approval_server.py
"""

import logging
import os
import threading
import uuid
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Silence Werkzeug's per-request HTTP log lines
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# In-memory store: only one pending request at a time
_lock = threading.Lock()
_pending: dict | None = None          # the current request waiting for decision
_events: dict[str, threading.Event] = {}  # request_id -> Event
_decisions: dict[str, bool] = {}         # request_id -> True=approved / False=rejected

# Live status broadcast
_status_lock = threading.Lock()
_current_status = {
    "state": "idle",      # "idle" | "speaking" | "working"
    "message": "",        # short human-readable description
    "updated_at": datetime.now().isoformat(),
}

PORT = 7845  # pick something unlikely to clash

VAULT_PATH = os.path.expanduser("~/Documents/Shiba-Vault")


# ── Status API (called by tools / Claude hook) ───────────────────────────────

def set_status(state: str, message: str = ""):
    """
    Update the live status visible in the Android app.
    state:   'idle' | 'speaking' | 'working'
    message: short description, e.g. 'Writing a file', 'Running a command'
    """
    with _status_lock:
        _current_status["state"] = state
        _current_status["message"] = message
        _current_status["updated_at"] = datetime.now().isoformat()


def clear_status():
    """Reset to idle after a task completes."""
    set_status("idle", "")


# ── Internal API (called by tools.py) ────────────────────────────────────────

def request_approval(action_type: str, summary: str, detail: str, timeout: int = 120) -> bool:
    """
    Block until the phone approves or rejects (or timeout expires).
    Returns True if approved, False otherwise.
    action_type: 'write_file' | 'execute_command'
    summary:     one-line description shown in the notification
    detail:      full content shown on the detail screen
    """
    req_id = str(uuid.uuid4())[:8]
    event = threading.Event()

    with _lock:
        global _pending
        _pending = {
            "id": req_id,
            "type": action_type,
            "summary": summary,
            "detail": detail,
            "created_at": datetime.now().isoformat(),
        }
        _events[req_id] = event

    print(f"\n[approval_server] Waiting for mobile approval (id={req_id}) …")

    approved = event.wait(timeout=timeout)

    with _lock:
        decision = _decisions.pop(req_id, False)
        _events.pop(req_id, None)
        if _pending and _pending.get("id") == req_id:
            _pending = None

    if not approved:
        print("[approval_server] Timed out — treating as rejected.")
        return False

    return decision


# ── HTTP endpoints (called by Android app) ────────────────────────────────────

@app.route("/approval/pending", methods=["GET"])
def pending():
    """Poll endpoint. Returns the current pending request or 204 if none."""
    with _lock:
        if _pending is None:
            return ("", 204)
        return jsonify(_pending)


@app.route("/approval/respond", methods=["POST"])
def respond():
    """
    Body: { "id": "<req_id>", "approved": true|false }
    """
    data = request.get_json(force=True, silent=True) or {}
    req_id = data.get("id")
    approved = bool(data.get("approved", False))

    with _lock:
        if req_id not in _events:
            return jsonify({"error": "unknown or expired request id"}), 404
        _decisions[req_id] = approved
        _events[req_id].set()

    status = "approved" if approved else "rejected"
    print(f"[approval_server] Request {req_id} → {status}")
    return jsonify({"status": status})


@app.route("/ping", methods=["GET"])
def ping():
    """Health-check so the app can verify it found the right server."""
    return jsonify({"service": "shiba-approval", "status": "ok"})


# ── Status endpoint ───────────────────────────────────────────────────────────

@app.route("/status", methods=["GET"])
def status():
    """
    Returns Shiba's current activity state for the mobile status bar.
    Response: { "state": "idle|speaking|working", "message": "...", "updated_at": "..." }
    """
    with _status_lock:
        return jsonify(dict(_current_status))


@app.route("/status/set", methods=["POST"])
def status_set():
    """
    Body: { "state": "speaking|working|idle", "message": "..." }
    Allows external tools to push status updates.
    """
    data = request.get_json(force=True, silent=True) or {}
    state = data.get("state", "idle")
    message = data.get("message", "")
    set_status(state, message)
    return jsonify({"ok": True})


# ── Vault endpoints ───────────────────────────────────────────────────────────

@app.route("/vault/list", methods=["GET"])
def vault_list():
    """Returns a list of all .md note filenames (without extension) in the vault."""
    if not os.path.isdir(VAULT_PATH):
        return jsonify({"error": "vault not found"}), 404
    notes = []
    for root, dirs, files in os.walk(VAULT_PATH):
        # skip hidden directories like .obsidian
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if f.endswith(".md"):
                rel = os.path.relpath(os.path.join(root, f), VAULT_PATH)
                notes.append(rel[:-3])  # strip .md
    notes.sort()
    return jsonify({"notes": notes})


@app.route("/vault/read", methods=["GET"])
def vault_read():
    """
    ?note=<relative path without .md>
    Returns the raw markdown content of that note.
    """
    note_name = request.args.get("note", "").strip()
    if not note_name:
        return jsonify({"error": "missing ?note= parameter"}), 400

    # Sanitise: prevent path traversal
    safe_name = os.path.normpath(note_name)
    if safe_name.startswith(".."):
        return jsonify({"error": "invalid note path"}), 400

    note_path = os.path.join(VAULT_PATH, safe_name + ".md")
    if not os.path.isfile(note_path):
        return jsonify({"error": "note not found"}), 404

    with open(note_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    return jsonify({"note": note_name, "content": content})


# ── Entry point ───────────────────────────────────────────────────────────────

def start_background():
    """Start the server in a daemon thread (called from tools.py on import)."""
    t = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=PORT, use_reloader=False),
        daemon=True,
        name="approval-server",
    )
    t.start()
    print(f"[approval_server] Listening on 0.0.0.0:{PORT}")


if __name__ == "__main__":
    print(f"Starting Shiba Approval Server on port {PORT} …")
    app.run(host="0.0.0.0", port=PORT, debug=False)
