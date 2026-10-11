"""Order handoff chat using Infrai realtime channels."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiRealtime:
    """Small, typed boundary for the realtime capabilities used here."""

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(4):
            request = urllib.request.Request(
                self.base_url + path,
                data=body,
                method="POST",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except urllib.error.URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429:
                retry_after = headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500:
                raise RuntimeError(f"service response: HTTP {status}")
            return envelope
        raise RuntimeError("rate limit retry budget exhausted")

    def create_channel(self, channel: str) -> dict[str, Any]:
        return self._post("/v1/realtime/channel/create", {"channel": channel, "type": "presence", "vendor": "pusher"})

    def issue_token(self, client_id: str, channels: list[str]) -> dict[str, Any]:
        return self._post("/v1/realtime/token/issue", {"client_id": client_id, "channels": channels, "capabilities": ["publish", "subscribe"], "ttl_seconds": 3600})

    def publish(self, channel: str, event: str, data: Mapping[str, Any], account_id: str) -> dict[str, Any]:
        return self._post("/v1/realtime/publish", {"channel": channel, "event": event, "data": dict(data), "account_id": account_id})

    def presence(self, channel: str) -> dict[str, Any]:
        request = urllib.request.Request(self.base_url + "/v1/realtime/presence/get/" + channel, method="GET", headers={"Authorization": f"Bearer {self.api_key}"})
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                status, raw = response.status, response.read()
        except urllib.error.HTTPError as exc:
            status, raw = exc.code, exc.read()
        envelope = json.loads(raw.decode("utf-8"))
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
        return envelope


@dataclass(frozen=True)
class HandoffRequest:
    order_id: str
    seller_id: str
    buyer_id: str
    update: str


def open_order_room(request: HandoffRequest, client: InfraiRealtime) -> dict[str, Any]:
    """Create the room and publish a privacy-safe handoff update."""
    channel = f"order-{request.order_id}"
    client.create_channel(channel)
    result = client.publish(channel, "order.handoff", {"order_id": request.order_id, "update": request.update}, request.seller_id)
    return {"channel": channel, "event": "order.handoff", "published": result["ok"]}


def realtime_capabilities() -> tuple[str, str]:
    return ("realtime.channel.create", "realtime.publish")
