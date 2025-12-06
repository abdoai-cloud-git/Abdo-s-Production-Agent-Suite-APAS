"""Client for triggering Make.com webhooks."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx


class MakeClient:
    """Wraps Make.com webhook invocations."""

    def __init__(self, *, base_url: Optional[str] = None, timeout: float = 10.0) -> None:
        self.base_url = base_url or os.getenv("MAKE_BASE_URL", "https://hook.eu1.make.com")
        self.timeout = timeout

    def trigger(self, hook_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not hook_key:
            raise ValueError("hook_key is required")
        url = f"{self.base_url.rstrip('/')}/{hook_key}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return {"status_code": response.status_code, "body": response.text}


if __name__ == "__main__":
    hook = os.getenv("MAKE_WEBHOOK_KEY")
    if not hook:
        print("Set MAKE_WEBHOOK_KEY to run the Make client demo.")
    else:
        client = MakeClient()
        print(client.trigger(hook, {"event": "demo", "value": 1}))
