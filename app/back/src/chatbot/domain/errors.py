"""Domain errors for chatbot question dispatch."""

from __future__ import annotations


class ChatbotDispatchError(Exception):
    """Base class for chatbot dispatch errors with stable public codes."""

    code = "CHATBOT_DISPATCH_ERROR"
    http_status = 400


class ChatbotWebhookNotConfigured(ChatbotDispatchError):
    """The webhook target is unavailable by configuration."""

    code = "CHATBOT_WEBHOOK_NOT_CONFIGURED"
    http_status = 503


class ChatbotWebhookDeliveryFailed(ChatbotDispatchError):
    """The webhook target rejected or failed the delivery."""

    code = "CHATBOT_WEBHOOK_DELIVERY_FAILED"
    http_status = 502


class ChatbotReleaseLaneUnavailable(ChatbotDispatchError):
    """The release does not resolve exactly one active retrieval lane."""

    code = "CHATBOT_RELEASE_LANE_UNAVAILABLE"
    http_status = 409


class ChatbotEvidenceUnavailable(ChatbotDispatchError):
    """The selected RAG release produced no evidence for the question."""

    code = "CHATBOT_EVIDENCE_UNAVAILABLE"
    http_status = 409
