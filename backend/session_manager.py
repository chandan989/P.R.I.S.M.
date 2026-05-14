"""
P.R.I.S.M. Session Management

Manages user sessions for the audit endpoint with support for
session history, resumption, and cleanup.
"""

import logging
import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Session status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"
    EXPIRED = "expired"


@dataclass
class SessionMessage:
    """A message in a session."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Session:
    """A user session for audit queries."""

    session_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: SessionStatus = SessionStatus.ACTIVE
    messages: List[SessionMessage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Query results
    query: Optional[str] = None
    deliberation: Optional[Dict[str, Any]] = None
    claims: Optional[List[Dict[str, Any]]] = None
    confidence: Optional[Dict[str, Any]] = None
    answer: Optional[str] = None

    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session is expired."""
        expiry_time = self.updated_at + timedelta(minutes=timeout_minutes)
        return datetime.utcnow() > expiry_time

    def touch(self):
        """Update session timestamp."""
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in self.messages
            ],
            "metadata": self.metadata,
            "query": self.query,
            "deliberation": self.deliberation,
            "claims": self.claims,
            "confidence": self.confidence,
            "answer": self.answer
        }


class SessionManager:
    """
    Manages user sessions.

    Features:
    - In-memory session storage
    - Session expiration and cleanup
    - Session history tracking
    - Optional Redis backend for distributed sessions
    """

    def __init__(
        self,
        session_timeout_minutes: int = 30,
        cleanup_interval_seconds: int = 300,
        use_redis: bool = False,
        redis_url: Optional[str] = None
    ):
        """
        Initialize session manager.

        Args:
            session_timeout_minutes: Session timeout in minutes
            cleanup_interval_seconds: Cleanup interval in seconds
            use_redis: Whether to use Redis for session storage
            redis_url: Redis connection URL
        """
        self.session_timeout = session_timeout_minutes
        self.cleanup_interval = cleanup_interval_seconds
        self.use_redis = use_redis
        self.redis_url = redis_url

        # In-memory session storage
        self.sessions: Dict[str, Session] = {}

        # Redis client (if enabled)
        self.redis_client = None
        if use_redis:
            self._init_redis()

        # Start cleanup task
        self._cleanup_task = None

    def _init_redis(self):
        """Initialize Redis client."""
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(
                self.redis_url or "redis://localhost:6379/0",
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis session storage enabled")
        except ImportError:
            logger.warning("redis package not installed, using in-memory storage")
            self.use_redis = False
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.use_redis = False

    async def create_session(
        self,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Create a new session.

        Args:
            session_id: Optional session ID (auto-generated if not provided)
            metadata: Optional session metadata

        Returns:
            New session
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        session = Session(
            session_id=session_id,
            metadata=metadata or {}
        )

        # Store session
        if self.use_redis and self.redis_client:
            await self._save_to_redis(session)
        else:
            self.sessions[session_id] = session

        logger.info(f"Created session: {session_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session if found and not expired, None otherwise
        """
        if self.use_redis and self.redis_client:
            session = await self._load_from_redis(session_id)
        else:
            session = self.sessions.get(session_id)

        if session and session.is_expired(self.session_timeout):
            logger.info(f"Session expired: {session_id}")
            await self.delete_session(session_id)
            return None

        return session

    async def update_session(
        self,
        session_id: str,
        **updates
    ) -> Optional[Session]:
        """
        Update a session.

        Args:
            session_id: Session ID
            **updates: Fields to update

        Returns:
            Updated session if found, None otherwise
        """
        session = await self.get_session(session_id)
        if not session:
            return None

        # Update fields
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.touch()

        # Save session
        if self.use_redis and self.redis_client:
            await self._save_to_redis(session)
        else:
            self.sessions[session_id] = session

        return session

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> Optional[Session]:
        """
        Add a message to a session.

        Args:
            session_id: Session ID
            role: Message role ("user" or "assistant")
            content: Message content

        Returns:
            Updated session if found, None otherwise
        """
        session = await self.get_session(session_id)
        if not session:
            return None

        message = SessionMessage(role=role, content=content)
        session.messages.append(message)
        session.touch()

        # Save session
        if self.use_redis and self.redis_client:
            await self._save_to_redis(session)
        else:
            self.sessions[session_id] = session

        return session

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found
        """
        if self.use_redis and self.redis_client:
            await self.redis_client.delete(f"session:{session_id}")
            return True
        else:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Deleted session: {session_id}")
                return True
            return False

    async def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        if self.use_redis and self.redis_client:
            # Redis handles expiration automatically with TTL
            return

        expired_ids = [
            session_id
            for session_id, session in self.sessions.items()
            if session.is_expired(self.session_timeout)
        ]

        for session_id in expired_ids:
            await self.delete_session(session_id)

        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired sessions")

    async def start_cleanup_task(self):
        """Start the background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Started session cleanup task")

    async def stop_cleanup_task(self):
        """Stop the background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Stopped session cleanup task")

    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _save_to_redis(self, session: Session):
        """Save session to Redis."""
        if not self.redis_client:
            return

        key = f"session:{session.session_id}"
        data = json.dumps(session.to_dict())

        # Set with TTL
        ttl = self.session_timeout * 60
        await self.redis_client.setex(key, ttl, data)

    async def _load_from_redis(self, session_id: str) -> Optional[Session]:
        """Load session from Redis."""
        if not self.redis_client:
            return None

        key = f"session:{session_id}"
        data = await self.redis_client.get(key)

        if not data:
            return None

        try:
            session_dict = json.loads(data)

            # Convert back to Session object
            session = Session(
                session_id=session_dict["session_id"],
                created_at=datetime.fromisoformat(session_dict["created_at"]),
                updated_at=datetime.fromisoformat(session_dict["updated_at"]),
                status=SessionStatus(session_dict["status"]),
                metadata=session_dict.get("metadata", {}),
                query=session_dict.get("query"),
                deliberation=session_dict.get("deliberation"),
                claims=session_dict.get("claims"),
                confidence=session_dict.get("confidence"),
                answer=session_dict.get("answer")
            )

            # Reconstruct messages
            for msg_dict in session_dict.get("messages", []):
                session.messages.append(SessionMessage(
                    role=msg_dict["role"],
                    content=msg_dict["content"],
                    timestamp=datetime.fromisoformat(msg_dict["timestamp"])
                ))

            return session

        except Exception as e:
            logger.error(f"Failed to load session from Redis: {e}")
            return None

    def get_session_count(self) -> int:
        """Get the number of active sessions."""
        if self.use_redis:
            # For Redis, we'd need to scan keys
            return -1
        return len(self.sessions)

    async def shutdown(self):
        """Shutdown the session manager."""
        await self.stop_cleanup_task()

        if self.redis_client:
            await self.redis_client.close()


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


async def init_session_manager(
    session_timeout_minutes: int = 30,
    use_redis: bool = False,
    redis_url: Optional[str] = None
) -> SessionManager:
    """
    Initialize the global session manager.

    Args:
        session_timeout_minutes: Session timeout in minutes
        use_redis: Whether to use Redis for session storage
        redis_url: Redis connection URL

    Returns:
        Session manager instance
    """
    global _session_manager

    if _session_manager:
        await _session_manager.shutdown()

    _session_manager = SessionManager(
        session_timeout_minutes=session_timeout_minutes,
        use_redis=use_redis,
        redis_url=redis_url
    )

    await _session_manager.start_cleanup_task()

    return _session_manager
