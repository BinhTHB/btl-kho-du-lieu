import asyncio
import json
import threading
from collections import deque

loop = None
clients = set()
recent = deque(maxlen=120)
_lock = threading.Lock()


def bind_loop(running_loop) -> None:
    global loop
    loop = running_loop


def publish(event: dict) -> None:
    with _lock:
        recent.append(event)
    if loop is None:
        return
    message = json.dumps(event, ensure_ascii=False)
    asyncio.run_coroutine_threadsafe(_fanout(message), loop)


async def _fanout(message: str) -> None:
    dead = []
    for ws in list(clients):
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        clients.discard(ws)


def snapshot() -> list:
    with _lock:
        return list(recent)


def clear() -> None:
    with _lock:
        recent.clear()
