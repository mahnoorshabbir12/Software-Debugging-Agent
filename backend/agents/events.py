import asyncio
import json
from typing import Dict, Any, AsyncGenerator

class EventDispatcher:
    """
    Manages Server-Sent Events (SSE) streams for debugging sessions.
    Allows the backend agents to broadcast events to the connected frontend.
    """
    _queues: Dict[int, asyncio.Queue] = {}

    @classmethod
    def register_client(cls, session_id: int) -> asyncio.Queue:
        if session_id not in cls._queues:
            cls._queues[session_id] = asyncio.Queue()
        return cls._queues[session_id]

    @classmethod
    def remove_client(cls, session_id: int):
        cls._queues.pop(session_id, None)

    @classmethod
    def emit(cls, session_id: int, event_type: str, data: Dict[str, Any]):
        """
        Emits an event to the specific session.
        """
        if session_id in cls._queues:
            event_payload = {
                "type": event_type,
                "sessionId": session_id,
                **data
            }
            # We use put_nowait to not block synchronous agent code if we call it from an async context
            # In a real sync-to-async bridge, we might need a threadsafe put.
            try:
                # If called from a sync thread, we must use call_soon_threadsafe
                loop = asyncio.get_running_loop()
                loop.call_soon_threadsafe(cls._queues[session_id].put_nowait, event_payload)
            except RuntimeError:
                # Fallback if no running loop in the current thread (e.g. tests)
                pass

    @classmethod
    async def event_generator(cls, session_id: int, queue: asyncio.Queue) -> AsyncGenerator[str, None]:
        """
        Generator for SSE streaming.
        """
        try:
            while True:
                # Wait for the next event in the queue
                event = await queue.get()
                
                # Format for SSE
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            cls.remove_client(session_id)
            raise
