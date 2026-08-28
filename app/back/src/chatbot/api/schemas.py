"""HTTP request/response schemas for the chatbot-facing API."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ingestion.schemas.common import StrictModel


class DispatchChatbotQuestionSchema(StrictModel):
    """Request sent by the chatbot edge to resolve one concrete RAG release."""

    project_id: str = Field(min_length=1)
    rag_variant_id: str = Field(min_length=1)
    rag_release_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    conversation_id: str | None = None
    message_id: str | None = None
    top_k: int = Field(default=10, ge=1, le=25)


class RagReleaseSummarySchema(StrictModel):
    """Narrow, chatbot-facing view of one RAG release.

    Deliberately omits platform-admin-only fields (``corpus_snapshot_id``,
    ``target_binding_key``, ``configuration_version``, ``release_manifest_hash``,
    ``created_by``, ``reason``): the downstream chatbot backend only needs enough
    to know which releases exist and their lifecycle state, never the platform
    management shape exposed at ``/api/platform/*``.
    """

    rag_release_id: str
    project_id: str
    rag_variant_id: str
    state: str
    release_number: int
    created_at: datetime
    validated_at: datetime | None = None


class PaginatedRagReleaseSummariesSchema(StrictModel):
    """One page of :class:`RagReleaseSummarySchema` items."""

    items: list[RagReleaseSummarySchema]
    page: int
    page_size: int
    total_items: int
    total_pages: int
