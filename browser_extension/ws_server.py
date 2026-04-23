"""
Shiba Browser WebSocket Server
Runs on ws://localhost:9009 (WebSocket) and http://localhost:9010 (HTTP API)
Bridges the Firefox extension to Shiba's tool system.
"""

import asyncio
import json
import uuid
import websockets
import logging
from aiohttp import web

logging.basicConfig(level=logging.INFO, format="[ws_server] %(message)s")

# Holds the single connected extension client
extension_ws = None
# Pending command futures: id -> asyncio.Future
pending = {}


async def handler(websocket, path=None):
    global extension_ws
    extension_ws = websocket
    logging.info("Extension connected")

    try:
        async for raw in websocket:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                logging.warning(f"Bad JSON: {raw}")
                continue

            # Handle heartbeat ping from extension
            if msg.get("type") == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
                continue

            cmd_id = msg.get("id")
            if cmd_id and cmd_id in pending:
                future = pending.pop(cmd_id)
                if not future.done():
                    future.set_result(msg)
            else:
                logging.info(f"Unhandled message: {msg}")
    except websockets.exceptions.ConnectionClosed:
        logging.info("Extension disconnected")
    finally:
        extension_ws = None


async def send_command(command: str, params: dict = None, timeout: float = 15.0):
    """Send a command to the extension and wait for the response."""
    if extension_ws is None:
        raise RuntimeError("No extension connected")

    cmd_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    pending[cmd_id] = future

    payload = json.dumps({"id": cmd_id, "command": command, "params": params or {}})
    await extension_ws.send(payload)

    try:
        result = await asyncio.wait_for(future, timeout=timeout)
        if result.get("error"):
            raise RuntimeError(result["error"])
        return result.get("result")
    except asyncio.TimeoutError:
        pending.pop(cmd_id, None)
        raise TimeoutError(f"Command '{command}' timed out after {timeout}s")


# ── HTTP API ──────────────────────────────────────────────────────────────────

async def http_command(request):
    """POST /command  { "command": "...", "params": {...} }"""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    command = body.get("command")
    params = body.get("params", {})

    if not command:
        return web.json_response({"error": "Missing 'command' field"}, status=400)

    try:
        result = await send_command(command, params)
        return web.json_response({"result": result})
    except RuntimeError as e:
        return web.json_response({"error": str(e)}, status=503)
    except TimeoutError as e:
        return web.json_response({"error": str(e)}, status=504)


async def http_status(request):
    return web.json_response({"connected": extension_ws is not None})


def make_http_app():
    app = web.Application()
    app.router.add_post("/command", http_command)
    app.router.add_get("/status", http_status)
    return app


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    logging.info("Starting Shiba browser WS server on ws://localhost:9009")
    logging.info("Starting Shiba browser HTTP API on http://localhost:9010")

    ws_server = websockets.serve(handler, "localhost", 9009)

    http_app = make_http_app()
    runner = web.AppRunner(http_app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 9010)

    await asyncio.gather(
        ws_server.__aenter__(),
        site.start(),
        asyncio.Future()  # run forever
    )


if __name__ == "__main__":
    asyncio.run(main())
