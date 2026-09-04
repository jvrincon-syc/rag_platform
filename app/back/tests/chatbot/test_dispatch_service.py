"""PR-1 1.5: the retrieval profile reported by dispatch must be the one that searched."""

from __future__ import annotations

import pytest

from chatbot.application.ports import ChatbotReleaseLane, ChatbotReleaseRetrievalResult
from chatbot.application.service import (
    DispatchChatbotQuestionRequest,
    DispatchChatbotQuestionUseCase,
)
from chatbot.domain.models import ChatbotWebhookDeliveryResult, ChatbotWebhookPayload
from core.consumer_scope import ConsumerScope
from retrieval.domain.models import RetrievedEvidence


#: Deliberately different from what `RetrievalProfile.build(consumer_scope_id=...)`
#: would hash from the default `ConsumerScope` -- proves the dispatcher no longer
#: rebuilds its own identity.
_SEARCHED_PROFILE_ID = "retp_release-scoped-dispatch-not-sst-default"


def _evidence() -> RetrievedEvidence:
    return RetrievedEvidence(
        node_id="node-1",
        document_id="doc-1",
        parent_node_id=None,
        child_chunk_id="node-1",
        text="El comite de convivencia sesiona mensualmente.",
        score=0.91,
        source="vector",
        embedding_profile_id="bge-m3",
        corpus_version="corpus_v1",
        embedding_bundle_id="bundle-1",
    )


class _FakeReleaseRetrieval:
    """Search port whose reported identity differs from the dispatcher's own scope."""

    def __init__(self, *, retrieval_profile_id: str) -> None:
        self._retrieval_profile_id = retrieval_profile_id
        self.received_calls: list[dict[str, object]] = []

    def search(
        self,
        *,
        project_id: str,
        rag_variant_id: str,
        rag_release_id: str,
        question: str,
        top_k: int,
    ) -> ChatbotReleaseRetrievalResult:
        self.received_calls.append(
            {
                "project_id": project_id,
                "rag_variant_id": rag_variant_id,
                "rag_release_id": rag_release_id,
                "question": question,
                "top_k": top_k,
            }
        )
        return ChatbotReleaseRetrievalResult(
            lane=ChatbotReleaseLane(
                embedding_profile_id="bge-m3",
                indexing_target_id="it_bge",
                corpus_version="corpus_v1",
            ),
            evidence=(_evidence(),),
            retrieval_profile_id=self._retrieval_profile_id,
        )


class _RecordingWebhook:
    def __init__(self) -> None:
        self.delivered: ChatbotWebhookPayload | None = None

    def deliver(self, payload: ChatbotWebhookPayload) -> ChatbotWebhookDeliveryResult:
        self.delivered = payload
        return ChatbotWebhookDeliveryResult(
            delivery_id="del-1", target_url="https://example.test/webhook", status_code=200
        )


def _request() -> DispatchChatbotQuestionRequest:
    return DispatchChatbotQuestionRequest(
        project_id="proj_alpha",
        rag_variant_id="ragv_bge",
        rag_release_id="ragr_1",
        question="Que hace el comite de convivencia?",
    )


def test_dispatch_reporta_el_profile_que_busco() -> None:
    release_retrieval = _FakeReleaseRetrieval(retrieval_profile_id=_SEARCHED_PROFILE_ID)
    webhook = _RecordingWebhook()
    use_case = DispatchChatbotQuestionUseCase(
        release_retrieval=release_retrieval,
        # A default consumer scope that, pre-fix, was used to rebuild a SECOND,
        # different profile id ("sst-default"-derived) than the one that searched.
        consumer_scope=ConsumerScope(),
        webhook=webhook,
    )

    result = use_case.execute(_request())

    assert result.retrieval_profile_id == _SEARCHED_PROFILE_ID
    assert webhook.delivered is not None
    assert webhook.delivered.retrieval_profile_id == _SEARCHED_PROFILE_ID


def test_dispatch_no_reconstruye_un_profile_distinto_del_consumer_scope_por_defecto() -> None:
    # Guard against regressing back to `RetrievalProfile.build(consumer_scope_id=...)`:
    # a profile id built from the default scope must NOT be what gets reported.
    from retrieval.domain.models import RetrievalProfile

    rebuilt = RetrievalProfile.build(
        project_id="proj_alpha",
        consumer_scope_type="chatbot",
        consumer_scope_id=ConsumerScope().scope_id,
        corpus_version="corpus_v1",
        embedding_profile_id="bge-m3",
        indexing_target_id="it_bge",
    )
    release_retrieval = _FakeReleaseRetrieval(retrieval_profile_id=_SEARCHED_PROFILE_ID)
    use_case = DispatchChatbotQuestionUseCase(
        release_retrieval=release_retrieval,
        consumer_scope=ConsumerScope(),
        webhook=_RecordingWebhook(),
    )

    result = use_case.execute(_request())

    assert result.retrieval_profile_id != rebuilt.retrieval_profile_id
    assert result.retrieval_profile_id == _SEARCHED_PROFILE_ID
