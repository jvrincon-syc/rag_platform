"""Ports used by the chatbot dispatch use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from chatbot.domain.models import ChatbotWebhookDeliveryResult, ChatbotWebhookPayload
from retrieval.domain.models import RetrievedEvidence


class ChatbotWebhookDeliveryPort(Protocol):
    """Delivers the question + chunks payload to the downstream webhook."""

    def deliver(
        self,
        payload: ChatbotWebhookPayload,
    ) -> ChatbotWebhookDeliveryResult:
        """Deliver one payload and return safe transport metadata."""


@dataclass(frozen=True)
class ChatbotReleaseLane:
    """One published release resolved to exactly one retrieval lane."""

    embedding_profile_id: str
    indexing_target_id: str
    corpus_version: str


@dataclass(frozen=True)
class ChatbotReleaseRetrievalResult:
    """The release lane plus the evidence retrieved inside that release only."""

    lane: ChatbotReleaseLane
    evidence: tuple[RetrievedEvidence, ...]


class ChatbotReleaseRetrievalPort(Protocol):
    """Search one published release without relying on the active legacy lane."""

    def search(
        self,
        *,
        project_id: str,
        rag_variant_id: str,
        rag_release_id: str,
        question: str,
        top_k: int,
    ) -> ChatbotReleaseRetrievalResult:
        """Return release-scoped evidence or fail closed when the lane is ambiguous."""
