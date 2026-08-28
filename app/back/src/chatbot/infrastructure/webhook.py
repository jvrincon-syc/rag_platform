"""Webhook delivery adapters for chatbot question dispatch."""

from __future__ import annotations

from hashlib import sha256
import json
from urllib import error, request

from chatbot.domain.errors import (
    ChatbotWebhookDeliveryFailed,
    ChatbotWebhookNotConfigured,
)
from chatbot.domain.models import ChatbotWebhookDeliveryResult, ChatbotWebhookPayload


class MissingChatbotWebhookDispatcher:
    """Fail-closed dispatcher used when no webhook configuration exists."""

    def deliver(
        self,
        payload: ChatbotWebhookPayload,
    ) -> ChatbotWebhookDeliveryResult:
        raise ChatbotWebhookNotConfigured(
            "the chatbot webhook target is not configured"
        )


class ConfiguredChatbotWebhookDispatcher:
    """HTTP webhook delivery over the Python standard library."""

    def __init__(
        self,
        *,
        target_url: str,
        bearer_token: str | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._target_url = target_url
        self._bearer_token = bearer_token
        self._timeout_seconds = timeout_seconds

    def deliver(
        self,
        payload: ChatbotWebhookPayload,
    ) -> ChatbotWebhookDeliveryResult:
        body = json.dumps(
            payload.model_dump(mode="json"),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "chatbot-sst-webhook/1.0",
        }
        if self._bearer_token:
            headers["Authorization"] = f"Bearer {self._bearer_token}"
        http_request = request.Request(
            self._target_url,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=self._timeout_seconds) as response:
                status_code = int(response.getcode())
        except error.HTTPError as exc:
            raise ChatbotWebhookDeliveryFailed(
                f"chatbot webhook responded with HTTP {exc.code}"
            ) from exc
        except error.URLError as exc:
            raise ChatbotWebhookDeliveryFailed(
                "chatbot webhook could not be reached"
            ) from exc
        return ChatbotWebhookDeliveryResult(
            delivery_id="whd_" + sha256(body).hexdigest()[:24],
            target_url=self._target_url,
            status_code=status_code,
        )
