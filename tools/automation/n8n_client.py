"""Client for triggering n8n workflows."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx


class N8NClient:
    """Triggers n8n webhook URLs with JSON payloads."""

    def __init__(self, *, base_url: Optional[str] = None, timeout: float = 10.0) -> None:
        self.base_url = base_url or os.getenv("N8N_BASE_URL")
        self.timeout = timeout

    def trigger(self, path_or_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = self._resolve_url(path_or_url)
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            body: Any = None
            if response.content:
                try:
                    body = response.json()
                except ValueError:
                    body = response.text
            return {"status_code": response.status_code, "body": body}

    def _resolve_url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http"):
            return path_or_url
        if not self.base_url:
            raise ValueError("Set N8N_BASE_URL or pass a full URL")
        return f"{self.base_url.rstrip('/')}/{path_or_url.lstrip('/')}"


if __name__ == "__main__":
    url = os.getenv("N8N_WEBHOOK_URL")
    if not url and not os.getenv("N8N_BASE_URL"):
        print("Set N8N_WEBHOOK_URL or N8N_BASE_URL to run the n8n client demo.")
    else:
        client = N8NClient()
        print(client.trigger(url or "demo", {"status": "ok"}))
