"""Server-Sent Events (SSE) route for real-time monitoring updates."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Query, Request, status
from fastapi.responses import StreamingResponse

from app.core.logging import get_logger
from app.core.security import verify_token
from app.services.events import event_manager

logger = get_logger(__name__)

router = APIRouter(prefix="/events", tags=["Real-time Stream"])


@router.get("/stream")
async def stream_events(
    request: Request,
    token: str = Query(..., description="JWT Bearer token for EventSource authentication"),
):
    """Server-Sent Events (SSE) endpoint for live monitoring updates.

    Emits:
    - ping: periodic keep-alive
    - check_completed: when an endpoint health probe finishes
    - incident_created: when an outage/degradation incident is opened
    - incident_resolved: when an endpoint recovers
    """
    payload = verify_token(token)
    if not payload or not payload.get("sub"):
        return StreamingResponse(
            iter(["event: error\ndata: {\"error\": \"Unauthorized\"}\n\n"]),
            status_code=status.HTTP_401_UNAUTHORIZED,
            media_type="text/event-stream",
        )

    user_id = str(payload["sub"])
    queue = await event_manager.subscribe(user_id)

    async def event_generator() -> AsyncGenerator[str, None]:
        # Initial handshake event
        yield "event: connected\ndata: {\"status\": \"connected\"}\n\n"

        try:
            while True:
                # Disconnection check
                if await request.is_disconnected():
                    break

                try:
                    # Wait for next event or send ping keepalive after 15 seconds
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield event.format()
                except TimeoutError:
                    yield ": ping\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await event_manager.unsubscribe(user_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
