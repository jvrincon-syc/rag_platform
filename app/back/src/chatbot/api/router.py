"""HTTP routes for chatbot question dispatch."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query, Request, status

from chatbot.api.schemas import (
    DispatchChatbotQuestionSchema,
    PaginatedRagReleaseSummariesSchema,
    RagReleaseSummarySchema,
)
from chatbot.application.service import (
    DispatchChatbotQuestionRequest,
    DispatchChatbotQuestionUseCase,
)
from chatbot.domain.errors import ChatbotDispatchError
from chatbot.domain.models import ChatbotQuestionDispatchResult
from core.api.http import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    ErrorEnvelopeSchema,
    http_error,
    paginate,
)
from core.feature_flags import FeatureFlags
from core.logging.observability import EventStatus, ObservabilityDomain
from embedding.application.events import emit_pipeline_event
from rag_platform.api.dependencies import get_actor_provider
from rag_platform.application.actor_provider import TrustedPlatformActorProvider
from rag_platform.application.platform_access import PlatformActor
from rag_platform.domain.identity import IdentityKind, PlatformId
from rag_platform.domain.lifecycle import RagRelease

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/chatbot",
    tags=["chatbot"],
    responses={
        400: {"model": ErrorEnvelopeSchema},
        401: {"model": ErrorEnvelopeSchema},
        403: {"model": ErrorEnvelopeSchema},
        404: {"model": ErrorEnvelopeSchema},
        409: {"model": ErrorEnvelopeSchema},
        422: {"model": ErrorEnvelopeSchema},
        502: {"model": ErrorEnvelopeSchema},
        503: {"model": ErrorEnvelopeSchema},
    },
)


def require_chatbot_webhook_enabled(request: Request) -> None:
    flags: FeatureFlags = request.app.state.feature_flags
    if not flags.chatbot_webhook_v1:
        raise http_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="CHATBOT_WEBHOOK_V1_DISABLED",
            message="the chatbot_webhook_v1 feature flag is off",
        )


def get_dispatch_use_case(request: Request) -> DispatchChatbotQuestionUseCase:
    return request.app.state.chatbot_dispatch_question


def get_actor(
    provider: TrustedPlatformActorProvider = Depends(get_actor_provider),
) -> PlatformActor:
    return provider.current_actor()


def _parse_id(kind: IdentityKind, value: str) -> PlatformId:
    return PlatformId.parse(kind, value)


def _translate(error: Exception):
    return http_error(
        status_code=int(getattr(error, "http_status", 400)),
        code=getattr(error, "code", "CHATBOT_DISPATCH_ERROR"),
        message=str(error),
    )


def _request_attributes(
    payload: DispatchChatbotQuestionSchema,
) -> dict[str, str | int | bool]:
    return {
        "project_id": payload.project_id,
        "rag_variant_id": payload.rag_variant_id,
        "rag_release_id": payload.rag_release_id,
        "top_k": payload.top_k,
        "conversation_id_present": payload.conversation_id is not None,
        "message_id_present": payload.message_id is not None,
    }


def _emit_request_event(
    *,
    payload: DispatchChatbotQuestionSchema,
    status: EventStatus,
    event: str,
    message: str,
    reason: str | None = None,
    http_status: int | None = None,
    release_state: str | None = None,
    retrieval_profile_id: str | None = None,
    dispatch_id: str | None = None,
    chunks_sent: int | None = None,
    webhook_status_code: int | None = None,
) -> None:
    attributes: dict[str, str | int | bool] = _request_attributes(payload)
    if reason is not None:
        attributes["reason"] = reason
    if http_status is not None:
        attributes["http_status"] = http_status
    if release_state is not None:
        attributes["release_state"] = release_state
    if retrieval_profile_id is not None:
        attributes["retrieval_profile_id"] = retrieval_profile_id
    if dispatch_id is not None:
        attributes["dispatch_id"] = dispatch_id
    metrics: dict[str, int | float] = {}
    if chunks_sent is not None:
        metrics["chunks_sent"] = chunks_sent
    if webhook_status_code is not None:
        metrics["webhook_status_code"] = webhook_status_code
    emit_pipeline_event(
        logger=logger,
        domain=ObservabilityDomain.HTTP,
        event=event,
        status=status,
        message=message,
        capability="chatbot_dispatch_api",
        metrics=metrics,
        attributes=attributes,
    )


@router.post(
    "/questions",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ChatbotQuestionDispatchResult,
    dependencies=[Depends(require_chatbot_webhook_enabled)],
)
def dispatch_question(
    request: Request,
    payload: DispatchChatbotQuestionSchema,
    use_case: DispatchChatbotQuestionUseCase = Depends(get_dispatch_use_case),
    actor: PlatformActor = Depends(get_actor),
) -> dict:
    _emit_request_event(
        payload=payload,
        status=EventStatus.STARTED,
        event="chatbot_question_request_received",
        message="Chatbot question request received",
    )
    rag_platform = request.app.state.rag_platform
    if rag_platform is None:
        _emit_request_event(
            payload=payload,
            status=EventStatus.BLOCKED,
            event="chatbot_question_request_rejected",
            message="Chatbot question request rejected because rag platform is unavailable",
            reason="rag_platform_disabled",
            http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        raise http_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="RAG_PLATFORM_V1_DISABLED",
            message="the rag_platform_v1 feature flag is off",
        )
    release = rag_platform.get_release.execute(
        _parse_id(IdentityKind.RAG_RELEASE, payload.rag_release_id),
        actor=actor,
    )
    if release.project_id.value != payload.project_id:
        _emit_request_event(
            payload=payload,
            status=EventStatus.REJECTED,
            event="chatbot_question_request_rejected",
            message="Chatbot question request rejected because the release does not belong to the project",
            reason="release_project_mismatch",
            http_status=status.HTTP_409_CONFLICT,
        )
        raise http_error(
            status_code=status.HTTP_409_CONFLICT,
            code="CHATBOT_RAG_CONTEXT_MISMATCH",
            message="rag_release_id does not belong to the provided project_id",
        )
    if release.rag_variant_id.value != payload.rag_variant_id:
        _emit_request_event(
            payload=payload,
            status=EventStatus.REJECTED,
            event="chatbot_question_request_rejected",
            message="Chatbot question request rejected because the release does not belong to the variant",
            reason="release_variant_mismatch",
            http_status=status.HTTP_409_CONFLICT,
        )
        raise http_error(
            status_code=status.HTTP_409_CONFLICT,
            code="CHATBOT_RAG_CONTEXT_MISMATCH",
            message="rag_release_id does not belong to the provided rag_variant_id",
        )
    if str(release.state.value) != "published":
        _emit_request_event(
            payload=payload,
            status=EventStatus.BLOCKED,
            event="chatbot_question_request_rejected",
            message="Chatbot question request rejected because the release is not published",
            reason="release_not_published",
            http_status=status.HTTP_409_CONFLICT,
            release_state=str(release.state.value),
        )
        raise http_error(
            status_code=status.HTTP_409_CONFLICT,
            code="CHATBOT_RELEASE_NOT_PUBLISHED",
            message="the requested rag_release_id is not published",
        )
    try:
        result = use_case.execute(
            DispatchChatbotQuestionRequest(
                project_id=payload.project_id,
                rag_variant_id=payload.rag_variant_id,
                rag_release_id=payload.rag_release_id,
                question=payload.question,
                conversation_id=payload.conversation_id,
                message_id=payload.message_id,
                top_k=payload.top_k,
            )
        )
    except ChatbotDispatchError as error:
        raise _translate(error) from error
    _emit_request_event(
        payload=payload,
        status=EventStatus.COMPLETED,
        event="chatbot_question_request_accepted",
        message="Chatbot question request dispatched successfully",
        http_status=status.HTTP_202_ACCEPTED,
        retrieval_profile_id=result.retrieval_profile_id,
        dispatch_id=result.dispatch_id,
        chunks_sent=result.chunks_sent,
        webhook_status_code=result.webhook_status_code,
    )
    return result.model_dump(mode="json")


def _release_to_summary(release: RagRelease) -> RagReleaseSummarySchema:
    """Map a domain ``RagRelease`` to the narrow chatbot-facing shape.

    Omits platform-admin-only fields on purpose (see
    :class:`RagReleaseSummarySchema`); the downstream chatbot backend never
    needs the platform management shape served at ``/api/platform/*``.
    """

    return RagReleaseSummarySchema(
        rag_release_id=release.rag_release_id.value,
        project_id=release.project_id.value,
        rag_variant_id=release.rag_variant_id.value,
        state=release.state.value,
        release_number=release.release_number,
        created_at=release.created_at,
        validated_at=release.validated_at,
    )


@router.get(
    "/rag-releases",
    response_model=PaginatedRagReleaseSummariesSchema,
)
def list_rag_releases(
    request: Request,
    project_id: str = Query(min_length=1),
    rag_variant_id: str | None = Query(default=None, min_length=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    actor: PlatformActor = Depends(get_actor),
) -> dict:
    """List the releases of a project, scoped to what the chatbot edge needs.

    Reuses ``ListProjectReleasesUseCase`` (the same use case backing the
    platform-admin ``GET /api/platform/projects/{project_id}/releases``) and
    only maps its output to the narrower ``RagReleaseSummarySchema``; the
    fetching/authorization logic is not duplicated here.
    """

    rag_platform = request.app.state.rag_platform
    if rag_platform is None:
        emit_pipeline_event(
            logger=logger,
            domain=ObservabilityDomain.HTTP,
            event="chatbot_rag_releases_request_rejected",
            status=EventStatus.BLOCKED,
            message="Chatbot rag-releases request rejected because rag platform is unavailable",
            capability="chatbot_rag_releases_api",
            attributes={
                "project_id": project_id,
                "reason": "rag_platform_disabled",
                "http_status": status.HTTP_503_SERVICE_UNAVAILABLE,
            },
        )
        raise http_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="RAG_PLATFORM_V1_DISABLED",
            message="the rag_platform_v1 feature flag is off",
        )
    releases = rag_platform.list_project_releases.execute(
        _parse_id(IdentityKind.PROJECT, project_id), actor=actor
    )
    if rag_variant_id is not None:
        releases = tuple(
            release
            for release in releases
            if release.rag_variant_id.value == rag_variant_id
        )
    items = [_release_to_summary(release) for release in releases]
    emit_pipeline_event(
        logger=logger,
        domain=ObservabilityDomain.HTTP,
        event="chatbot_rag_releases_request_completed",
        status=EventStatus.COMPLETED,
        message="Chatbot rag-releases request completed",
        capability="chatbot_rag_releases_api",
        attributes={
            "project_id": project_id,
            "rag_variant_id": rag_variant_id or "",
            "http_status": status.HTTP_200_OK,
        },
        metrics={"releases_returned": len(items)},
    )
    return paginate(items, page=page, page_size=page_size)
