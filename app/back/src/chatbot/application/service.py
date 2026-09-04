"""Use case that resolves one RAG release and dispatches question + chunks."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from time import perf_counter

from chatbot.application.ports import (
    ChatbotReleaseRetrievalPort,
    ChatbotWebhookDeliveryPort,
)
from chatbot.domain.errors import (
    ChatbotDispatchError,
    ChatbotEvidenceUnavailable,
    ChatbotReleaseLaneUnavailable,
    ChatbotWebhookDeliveryFailed,
    ChatbotWebhookNotConfigured,
)
from chatbot.domain.models import (
    ChatbotQuestionDispatchResult,
    ChatbotWebhookChunk,
    ChatbotWebhookPayload,
)
from core.consumer_scope import ConsumerScope
from core.logging.observability import (
    EventStatus,
    ObservabilityDomain,
    measure_duration_ms,
)
from embedding.application.events import emit_pipeline_event

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DispatchChatbotQuestionRequest:
    """Request accepted by the chatbot dispatch use case."""

    project_id: str
    rag_variant_id: str
    rag_release_id: str
    question: str
    conversation_id: str | None = None
    message_id: str | None = None
    top_k: int = 10


class DispatchChatbotQuestionUseCase:
    """Resolve one active release lane and forward its evidence by webhook."""

    def __init__(
        self,
        *,
        release_retrieval: ChatbotReleaseRetrievalPort,
        consumer_scope: ConsumerScope,
        webhook: ChatbotWebhookDeliveryPort,
    ) -> None:
        self._release_retrieval = release_retrieval
        self._consumer_scope = consumer_scope
        self._webhook = webhook

    def execute(
        self,
        request: DispatchChatbotQuestionRequest,
    ) -> ChatbotQuestionDispatchResult:
        dispatch_started_at = perf_counter()
        try:
            search_result = self._release_retrieval.search(
                project_id=request.project_id,
                rag_variant_id=request.rag_variant_id,
                rag_release_id=request.rag_release_id,
                question=request.question,
                top_k=request.top_k,
            )
            lane = search_result.lane
            # PR-1 1.5: reuse the exact profile identity the port used to search
            # (`_release_profile` in `release_scoped_retrieval.py`) instead of
            # rebuilding a second `RetrievalProfile` from `self._consumer_scope` --
            # that rebuild hashed a different `consumer_scope_id` and reported an
            # id that never matched the one that actually ran the query.
            retrieval_profile_id = search_result.retrieval_profile_id
            emit_pipeline_event(
                logger=logger,
                domain=ObservabilityDomain.BACKEND,
                event="chatbot_release_lane_resolved",
                status=EventStatus.COMPLETED,
                message="Chatbot dispatch resolved one release-scoped lane",
                capability="chatbot_dispatch",
                metrics={"matching_run_count": 1},
                attributes={
                    **self._request_attributes(request),
                    "embedding_profile_id": lane.embedding_profile_id,
                    "indexing_target_id": lane.indexing_target_id,
                    "corpus_version": lane.corpus_version,
                    "retrieval_profile_id": retrieval_profile_id,
                },
            )
            retrieval_started_at = perf_counter()
            evidence = list(search_result.evidence)
            retrieved_chunk_count = len(evidence)
            if not evidence:
                raise ChatbotEvidenceUnavailable(
                    "the selected RAG release produced no evidence for the requested question"
                )
            emit_pipeline_event(
                logger=logger,
                domain=ObservabilityDomain.BACKEND,
                event="chatbot_evidence_retrieved",
                status=EventStatus.COMPLETED,
                message="Chatbot dispatch retrieved evidence for the requested release",
                capability="chatbot_dispatch",
                metrics={
                    "retrieved_chunk_count": retrieved_chunk_count,
                    "chunks_after_release_filter": len(evidence),
                    "retrieval_duration_ms": measure_duration_ms(retrieval_started_at),
                },
                attributes={
                    **self._request_attributes(request),
                    "retrieval_profile_id": retrieval_profile_id,
                    "embedding_profile_id": lane.embedding_profile_id,
                    "corpus_version": lane.corpus_version,
                },
            )
            payload = ChatbotWebhookPayload.build(
                project_id=request.project_id,
                rag_variant_id=request.rag_variant_id,
                rag_release_id=request.rag_release_id,
                retrieval_profile_id=retrieval_profile_id,
                question=request.question,
                conversation_id=request.conversation_id,
                message_id=request.message_id,
                top_k=request.top_k,
                chunks=[ChatbotWebhookChunk.from_evidence(item) for item in evidence],
            )
            webhook_started_at = perf_counter()
            delivery = self._webhook.deliver(payload)
            emit_pipeline_event(
                logger=logger,
                domain=ObservabilityDomain.BACKEND,
                event="chatbot_webhook_dispatch_completed",
                status=EventStatus.COMPLETED,
                message="Chatbot dispatch delivered question and evidence to the webhook",
                capability="chatbot_dispatch",
                metrics={
                    "chunks_sent": len(payload.chunks),
                    "webhook_status_code": delivery.status_code,
                    "webhook_duration_ms": measure_duration_ms(webhook_started_at),
                    "dispatch_duration_ms": measure_duration_ms(dispatch_started_at),
                },
                attributes={
                    **self._request_attributes(request),
                    "dispatch_id": payload.dispatch_id,
                    "retrieval_profile_id": retrieval_profile_id,
                },
            )
            return ChatbotQuestionDispatchResult(
                dispatch_id=payload.dispatch_id,
                project_id=payload.project_id,
                rag_variant_id=payload.rag_variant_id,
                rag_release_id=payload.rag_release_id,
                retrieval_profile_id=payload.retrieval_profile_id,
                question=payload.question,
                conversation_id=payload.conversation_id,
                message_id=payload.message_id,
                chunks_sent=len(payload.chunks),
                webhook_status_code=delivery.status_code,
                dispatched_at=payload.dispatched_at,
            )
        except ChatbotDispatchError as error:
            self._emit_failure_event(
                request=request,
                error=error,
                dispatch_duration_ms=measure_duration_ms(dispatch_started_at),
            )
            raise

    @staticmethod
    def _request_attributes(
        request: DispatchChatbotQuestionRequest,
    ) -> dict[str, str | int | bool]:
        return {
            "project_id": request.project_id,
            "rag_variant_id": request.rag_variant_id,
            "rag_release_id": request.rag_release_id,
            "top_k": request.top_k,
            "conversation_id_present": request.conversation_id is not None,
            "message_id_present": request.message_id is not None,
        }

    def _emit_failure_event(
        self,
        *,
        request: DispatchChatbotQuestionRequest,
        error: ChatbotDispatchError,
        dispatch_duration_ms: int,
    ) -> None:
        event = "chatbot_question_dispatch_failed"
        message = "Chatbot dispatch failed"
        status = EventStatus.FAILED
        if isinstance(error, ChatbotReleaseLaneUnavailable):
            event = "chatbot_release_lane_unavailable"
            message = "Chatbot dispatch could not resolve one release-scoped lane"
            status = EventStatus.BLOCKED
        elif isinstance(error, ChatbotEvidenceUnavailable):
            event = "chatbot_evidence_unavailable"
            message = "Chatbot dispatch produced no evidence for the requested release"
            status = EventStatus.BLOCKED
        elif isinstance(
            error,
            (ChatbotWebhookNotConfigured, ChatbotWebhookDeliveryFailed),
        ):
            event = "chatbot_webhook_dispatch_failed"
            message = "Chatbot dispatch could not deliver the webhook payload"
            status = (
                EventStatus.BLOCKED
                if isinstance(error, ChatbotWebhookNotConfigured)
                else EventStatus.FAILED
            )
        emit_pipeline_event(
            logger=logger,
            domain=ObservabilityDomain.BACKEND,
            event=event,
            status=status,
            message=message,
            capability="chatbot_dispatch",
            metrics={"dispatch_duration_ms": dispatch_duration_ms},
            attributes={
                **self._request_attributes(request),
                "error_code": error.code,
                "http_status": error.http_status,
            },
            exception=error,
        )
