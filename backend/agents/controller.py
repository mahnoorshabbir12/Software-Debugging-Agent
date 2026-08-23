import threading
from typing import Dict

class AgentController:
    """
    Manages active agent sessions and handles cancellation and pausing.
    """
    _cancellation_flags: Dict[int, threading.Event] = {}
    _pause_flags: Dict[int, threading.Event] = {}

    @classmethod
    def register_session(cls, session_id: int):
        cls._cancellation_flags[session_id] = threading.Event()
        cls._pause_flags[session_id] = threading.Event()
        # pause flag is set when NOT paused (meaning allowed to run)
        cls._pause_flags[session_id].set()

    @classmethod
    def request_cancellation(cls, session_id: int):
        if session_id in cls._cancellation_flags:
            cls._cancellation_flags[session_id].set()

    @classmethod
    def request_pause(cls, session_id: int):
        if session_id in cls._pause_flags:
            cls._pause_flags[session_id].clear()

    @classmethod
    def request_resume(cls, session_id: int):
        if session_id in cls._pause_flags:
            cls._pause_flags[session_id].set()

    @classmethod
    def is_cancelled(cls, session_id: int) -> bool:
        if session_id in cls._cancellation_flags:
            return cls._cancellation_flags[session_id].is_set()
        return False

    @classmethod
    def wait_if_paused(cls, session_id: int, timeout: float = 1.0):
        """
        Agent loops should call this. It will block if the session is paused.
        It times out to allow the agent to check cancellation.
        """
        if session_id in cls._pause_flags:
            cls._pause_flags[session_id].wait(timeout)
            
    @classmethod
    def cleanup_session(cls, session_id: int):
        cls._cancellation_flags.pop(session_id, None)
        cls._pause_flags.pop(session_id, None)

class AgentCancelledException(Exception):
    pass
