"""Generic webhook trigger utility."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx


class WebhookTrigger:
    """POSTs JSON payloads to arbitrary webhook endpoints."""

    def __init__(self, *, timeout: float = 10.0, default_headers: Optional[Dict[str, str]] = None) -> None:
        self.timeout = timeout
        self.default_headers = default_headers or {"User-Agent": "APASWebhook/1.0"}

    def send(self, url: str, payload: Dict[str, Any], *, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        merged_headers = {**self.default_headers, **(headers or {})}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload, headers=merged_headers)
            response.raise_for_status()
            body: Any = None
            if response.content:
                try:
                    body = response.json()
                except ValueError:
                    body = response.text
            return {"status_code": response.status_code, "body": body}


if __name__ == "__main__":
    demo_url = os.getenv("WEBHOOK_URL")
    if not demo_url:
        print("Set WEBHOOK_URL to test the webhook trigger.")
    else:
        trigger = WebhookTrigger()
        print(trigger.send(demo_url, {"ping": "pong"}))
