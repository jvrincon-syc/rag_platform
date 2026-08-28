"""Pydantic contracts for chatbot webhook dispatch."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import PurePosixPath

from pydantic import Field

from ingestion.schemas.common import StrictModel
from retrieval.domain.models import RetrievedEvidence


def _now() -> datetime:
    return datetime.now(UTC)


def _dispatch_id(
    *,
    project_id: str,
    rag_variant_id: str,
    rag_release_id: str,
    question: str,
    conversation_id: str | None,
    message_id: str | None,
) -> str:
    payload = json.dumps(
        {
            "project_id": project_id,
            "rag_variant_id": rag_variant_id,
            "rag_release_id": rag_release_id,
            "question": question,
            "conversation_id": conversation_id,
            "message_id": message_id,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return "chatq_" + sha256(payload.encode("utf-8")).hexdigest()[:24]


class ChatbotWebhookChunk(StrictModel):
    """One retrieved chunk forwarded to the final answering webhook."""

    node_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    document_name: str = Field(min_length=1)
    parent_node_id: str | None = None
    child_chunk_id: str = Field(min_length=1)
    text: str
    score: float
    source: str = Field(min_length=1)
    page_start: int | None = None
    page_end: int | None = None
    section_title: str | None = None
    section_path: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    embedding_profile_id: str = Field(min_length=1)
    corpus_version: str = Field(min_length=1)
    embedding_bundle_id: str | None = None

    @classmethod
    def from_evidence(cls, evidence: RetrievedEvidence) -> "ChatbotWebhookChunk":
        # El contrato externo (.NET) deserializa ``metadata`` como
        # ``Dictionary<string, string?>`` (docs/other-backend-handoff.md):
        # valores no-string (p. ej. ``page_number`` int o ``retrieval_sources``
        # list, agregados por ``ParentExpansionService``) rompen ese binding con
        # un 400. Se serializan a string en el borde de salida del webhook, sin
        # tocar el ``metadata`` interno de retrieval ni debilitar validación.
        data = evidence.model_dump(mode="json")
        document_name = _resolve_document_name(evidence)
        raw_metadata = dict(data.get("metadata", {}))
        raw_metadata["document_name"] = document_name
        data["document_name"] = document_name
        data["metadata"] = {
            key: value if value is None or isinstance(value, str) else json.dumps(value)
            for key, value in raw_metadata.items()
        }
        return cls(**data)


def _resolve_document_name(evidence: RetrievedEvidence) -> str:
    metadata_name = evidence.metadata.get("document_name")
    if isinstance(metadata_name, str) and metadata_name.strip():
        return metadata_name.strip()
    source_relpath = evidence.metadata.get("source_relpath")
    if isinstance(source_relpath, str) and source_relpath.strip():
        return PurePosixPath(source_relpath.strip()).name
    return evidence.document_id


class ChatbotWebhookPayload(StrictModel):
    """Payload delivered to the downstream webhook."""

    dispatch_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    rag_variant_id: str = Field(min_length=1)
    rag_release_id: str = Field(min_length=1)
    retrieval_profile_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    conversation_id: str | None = None
    message_id: str | None = None
    top_k: int = Field(ge=1)
    chunks: list[ChatbotWebhookChunk] = Field(default_factory=list)
    dispatched_at: datetime = Field(default_factory=_now)

    @classmethod
    def build(
        cls,
        *,
        project_id: str,
        rag_variant_id: str,
        rag_release_id: str,
        retrieval_profile_id: str,
        question: str,
        conversation_id: str | None,
        message_id: str | None,
        top_k: int,
        chunks: list[ChatbotWebhookChunk],
    ) -> "ChatbotWebhookPayload":
        return cls(
            dispatch_id=_dispatch_id(
                project_id=project_id,
                rag_variant_id=rag_variant_id,
                rag_release_id=rag_release_id,
                question=question,
                conversation_id=conversation_id,
                message_id=message_id,
            ),
            project_id=project_id,
            rag_variant_id=rag_variant_id,
            rag_release_id=rag_release_id,
            retrieval_profile_id=retrieval_profile_id,
            question=question,
            conversation_id=conversation_id,
            message_id=message_id,
            top_k=top_k,
            chunks=chunks,
        )


class ChatbotWebhookDeliveryResult(StrictModel):
    """Safe delivery metadata returned by the webhook adapter."""

    delivery_id: str = Field(min_length=1)
    target_url: str = Field(min_length=1)
    status_code: int = Field(ge=100, le=599)


class ChatbotQuestionDispatchResult(StrictModel):
    """Public HTTP response after dispatching a question to the webhook."""

    dispatch_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    rag_variant_id: str = Field(min_length=1)
    rag_release_id: str = Field(min_length=1)
    retrieval_profile_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    conversation_id: str | None = None
    message_id: str | None = None
    chunks_sent: int = Field(ge=0)
    webhook_status_code: int = Field(ge=100, le=599)
    dispatched_at: datetime = Field(default_factory=_now)
