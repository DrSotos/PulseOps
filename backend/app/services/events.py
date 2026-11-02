"""In-memory Server-Sent Events (SSE) broker for real-time monitoring updates."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SSEEvent:
    event: str
    data: dict[str, Any]
    id: str | None = None

    def format(self) -> str:
        lines: list[str] = []
        if self.id:
            lines.append(f"id: {self.id}")
        lines.append(f"event: {self.event}")
        lines.append(f"data: {json.dumps(self.data)}")
        lines.append("\n")
        return "\n".join(lines)


class SSEEventManager:
    """Manages real-time SSE streams per authenticated user."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[asyncio.Queue[SSEEvent]]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, user_id: str) -> asyncio.Queue[SSEEvent]:
        queue: asyncio.Queue[SSEEvent] = asyncio.Queue(maxsize=150)
        async with self._lock:
            if user_id not in self._listeners:
                self._listeners[user_id] = []
            self._listeners[user_id].append(queue)
        logger.debug(f"User {user_id} subscribed to SSE. Total active listeners: {len(self._listeners[user_id])}")
        return queue

    async def unsubscribe(self, user_id: str, queue: asyncio.Queue[SSEEvent]) -> None:
        async with self._lock:
            if user_id in self._listeners:
                if queue in self._listeners[user_id]:
                    self._listeners[user_id].remove(queue)
                if not self._listeners[user_id]:
                    del self._listeners[user_id]
        logger.debug(f"User {user_id} unsubscribed from SSE.")

    async def publish_to_user(self, user_id: str, event_type: str, data: dict[str, Any]) -> None:
        event = SSEEvent(event=event_type, data=data)
        async with self._lock:
            queues = list(self._listeners.get(user_id, []))

        for q in queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"Dropping event '{event_type}' for user {user_id} (queue full)")

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        event = SSEEvent(event=event_type, data=data)
        async with self._lock:
            all_queues = [q for queues in self._listeners.values() for q in queues]

        for q in all_queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass


event_manager = SSEEventManager()
