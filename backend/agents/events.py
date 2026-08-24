import asyncio
import json
from typing import Dict, Any, AsyncGenerator, Optional


class EventDispatcher:
    """
    Manages Server-Sent Events (SSE) streams for debugging sessions.
    
    The key challenge: the background investigation runner runs in a sync thread,
    but the SSE queue consumers run in the asyncio event loop. We bridge this by
    storing a reference to the event loop when a client registers, then using
    call_soon_threadsafe() to push events from the sync thread.
    """
    _queues: Dict[int, asyncio.Queue] = {}
    _loop: Optional[asyncio.AbstractEventLoop] = None

    @classmethod
    def register_client(cls, session_id: int) -> asyncio.Queue:
        """Called from within an async request handler — safe to grab the loop."""
        if session_id not in cls._queues:
            cls._queues[session_id] = asyncio.Queue()
        # Capture the running event loop so background threads can push to it
        try:
            cls._loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        return cls._queues[session_id]

    @classmethod
    def remove_client(cls, session_id: int):
        cls._queues.pop(session_id, None)

    @classmethod
    def emit(cls, session_id: int, event_type: str, data: Dict[str, Any]):
        """
        Emits an event to the specific session's SSE stream.
        
        Safe to call from both sync threads (background runner) and async contexts.
        """
        if session_id not in cls._queues:
            return
            
        event_payload = {
            "type": event_type,
            "sessionId": session_id,
            **data
        }
        
        queue = cls._queues[session_id]
        
        # Try to detect if we're in the event loop thread
        try:
            running_loop = asyncio.get_running_loop()
            # We're inside the event loop — safe to put directly
            queue.put_nowait(event_payload)
        except RuntimeError:
            # We're in a background thread — use the stored loop reference
            if cls._loop and cls._loop.is_running():
                cls._loop.call_soon_threadsafe(queue.put_nowait, event_payload)

    @classmethod
    async def event_generator(cls, session_id: int, queue: asyncio.Queue) -> AsyncGenerator[str, None]:
        """
        Async generator that yields SSE-formatted events from the queue.
        """
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            cls.remove_client(session_id)
            raise

