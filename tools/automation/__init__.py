"""Automation connectors."""

from .email_sender import EmailSender
from .make_client import MakeClient
from .n8n_client import N8NClient
from .webhook_trigger import WebhookTrigger

__all__ = ["EmailSender", "WebhookTrigger", "MakeClient", "N8NClient"]
