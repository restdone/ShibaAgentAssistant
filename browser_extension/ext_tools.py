"""
Shiba extension-based browser tools.
These call the HTTP API on ws_server.py (port 9010), which relays commands to Firefox.
The WebSocket on port 9009 is reserved exclusively for the Firefox extension.
"""

import requests

HTTP_URL = "http://localhost:9010"


def _send(command: str, params: dict = None, timeout: float = 20.0):
    payload = {"command": command, "params": params or {}}
    try:
        resp = requests.post(f"{HTTP_URL}/command", json=payload, timeout=timeout)
        data = resp.json()
        if "error" in data:
            raise RuntimeError(data["error"])
        return data.get("result")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("WebSocket server is not running. Start it with ws_server.py.")


def get_status():
    """Check if the Firefox extension is connected."""
    try:
        resp = requests.get(f"{HTTP_URL}/status", timeout=5)
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"connected": False, "error": "Server not running"}


# --- Tool functions ---

def ext_get_info():
    """Get current tab URL and title."""
    return _send("get_info")

def ext_navigate(url: str):
    """Navigate the active tab to a URL."""
    return _send("navigate", {"url": url})

def ext_get_text():
    """Get visible text content of the current page."""
    return _send("get_text")

def ext_click(selector: str):
    """Click an element by CSS selector."""
    return _send("click", {"selector": selector})

def ext_type(selector: str, text: str):
    """Type text into an element by CSS selector."""
    return _send("type", {"selector": selector, "text": text})

def ext_scroll(y: int = 500):
    """Scroll down the page."""
    return _send("scroll", {"y": y})

def ext_screenshot():
    """Take a screenshot of the current tab (returns base64 PNG data URL)."""
    return _send("screenshot")

def ext_evaluate(code: str):
    """Run JavaScript in the current page and return the result."""
    return _send("evaluate", {"code": code})

def ext_open_new_tab(url: str = None):
    """Open a new tab in Firefox. Optionally navigate to a URL."""
    params = {"url": url} if url else {}
    return _send("open_tab", params)
