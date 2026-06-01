"""ConversationState Manager — Enhancement 017 Phase 2.

Manages multi-step conversation state and context handoffs across requests.
Enables Task → Plan → Execute pipeline with persistent context between turns.

The CollaborationManager already handles context within a single request via
shared_context dicts. This module extends that to persist state across multiple
requests in the same logical conversation.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import structlog


class StateStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StepResult:
    """Record of one completed provider step."""
    step_index: int
    provider: str
    content: str
    tokens_used: int
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConversationState:
    """Multi-step conversation state for one logical conversation.

    Tracks context accumulated across provider steps so each subsequent
    provider receives full context from prior steps without the caller
    having to re-assemble it.
    """
    conversation_id: str
    original_request: str
    status: StateStatus = StateStatus.PENDING
    current_step: int = 0
    total_steps: int = 0
    steps: List[StepResult] = field(default_factory=list)
    accumulated_context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: int = 1800

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl_seconds)

    @property
    def context_for_next_step(self) -> str:
        """Build full context string for the next provider."""
        if not self.steps:
            return self.original_request
        parts = [f"Original request: {self.original_request}\n"]
        for s in self.steps:
            parts.append(f"[Step {s.step_index + 1} — {s.provider}]:\n{s.content}")
        return "\n\n".join(parts)

    def add_step(
        self,
        provider: str,
        content: str,
        tokens: int = 0,
        exec_time: float = 0.0,
    ) -> StepResult:
        result = StepResult(
            step_index=self.current_step,
            provider=provider,
            content=content,
            tokens_used=tokens,
            execution_time=exec_time,
        )
        self.steps.append(result)
        self.accumulated_context += f"\n[{provider}]: {content}"
        self.current_step += 1
        self.updated_at = datetime.utcnow()
        return result

    def total_tokens(self) -> int:
        return sum(s.tokens_used for s in self.steps)

    def is_complete(self) -> bool:
        return self.total_steps > 0 and self.current_step >= self.total_steps

    def summary(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "status": self.status.value,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "total_tokens": self.total_tokens(),
            "providers_used": [s.provider for s in self.steps],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ConversationStateManager:
    """In-memory store for ConversationState objects with TTL eviction.

    Designed as a singleton (use get_state_manager()). Optional Redis/MongoDB
    persistence can be layered on top without changing this interface.
    """

    def __init__(self, ttl_seconds: int = 1800, max_states: int = 1000) -> None:
        self._states: Dict[str, ConversationState] = {}
        self.ttl_seconds = ttl_seconds
        self.max_states = max_states
        self.logger = structlog.get_logger().bind(component="state_manager")

    def create(
        self,
        conversation_id: str,
        original_request: str,
        total_steps: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationState:
        if len(self._states) >= self.max_states:
            self._evict_expired()

        state = ConversationState(
            conversation_id=conversation_id,
            original_request=original_request,
            total_steps=total_steps,
            metadata=metadata or {},
            ttl_seconds=self.ttl_seconds,
        )
        self._states[conversation_id] = state
        self.logger.info("state_created", conversation_id=conversation_id, total_steps=total_steps)
        return state

    def get(self, conversation_id: str) -> Optional[ConversationState]:
        """Return state or None if not found / expired."""
        state = self._states.get(conversation_id)
        if state is None:
            return None
        if state.is_expired:
            del self._states[conversation_id]
            self.logger.info("state_expired_evicted", conversation_id=conversation_id)
            return None
        return state

    def get_or_create(
        self,
        conversation_id: str,
        original_request: str,
        total_steps: int = 0,
    ) -> ConversationState:
        state = self.get(conversation_id)
        if state is None:
            state = self.create(conversation_id, original_request, total_steps)
        return state

    def update_step(
        self,
        conversation_id: str,
        provider: str,
        content: str,
        tokens: int = 0,
        exec_time: float = 0.0,
    ) -> Optional[StepResult]:
        """Record a completed step. Returns None if state not found."""
        state = self.get(conversation_id)
        if state is None:
            self.logger.warning("state_not_found", conversation_id=conversation_id)
            return None

        result = state.add_step(provider, content, tokens, exec_time)
        state.status = StateStatus.COMPLETED if state.is_complete() else StateStatus.IN_PROGRESS

        if state.status == StateStatus.COMPLETED:
            self.logger.info(
                "state_completed",
                conversation_id=conversation_id,
                total_steps=state.total_steps,
                total_tokens=state.total_tokens(),
            )
        return result

    def mark_failed(self, conversation_id: str, reason: str = "") -> None:
        state = self.get(conversation_id)
        if state:
            state.status = StateStatus.FAILED
            state.metadata["failure_reason"] = reason
            state.updated_at = datetime.utcnow()

    def get_context(self, conversation_id: str) -> str:
        """Return accumulated context for passing to the next provider."""
        state = self.get(conversation_id)
        return state.context_for_next_step if state else ""

    def delete(self, conversation_id: str) -> None:
        self._states.pop(conversation_id, None)

    def _evict_expired(self) -> int:
        expired = [cid for cid, s in self._states.items() if s.is_expired]
        for cid in expired:
            del self._states[cid]
        if expired:
            self.logger.info("expired_states_evicted", count=len(expired))
        return len(expired)

    def stats(self) -> Dict[str, Any]:
        self._evict_expired()
        status_counts: Dict[str, int] = {}
        for s in self._states.values():
            status_counts[s.status.value] = status_counts.get(s.status.value, 0) + 1
        return {
            "active_states": len(self._states),
            "status_breakdown": status_counts,
            "ttl_seconds": self.ttl_seconds,
            "max_states": self.max_states,
        }


_state_manager: Optional[ConversationStateManager] = None


def get_state_manager() -> ConversationStateManager:
    global _state_manager
    if _state_manager is None:
        _state_manager = ConversationStateManager()
    return _state_manager
