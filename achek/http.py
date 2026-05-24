from __future__ import annotations

import json
import time
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .exceptions import AchekConnectError

# HTTP status codes that are safe to retry (transient errors)
_RETRYABLE_STATUSES: frozenset[int] = frozenset({429, 500, 502, 503, 504})


class HttpClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: int,
        max_attempts: int = 3,
        initial_delay_ms: int = 500,
    ) -> None:
        self._api_key         = api_key
        self._base_url        = base_url.rstrip("/")
        self._timeout         = timeout
        self._max_attempts    = max_attempts
        self._initial_delay_s = initial_delay_ms / 1000

    def _request(
        self,
        method: str,
        path: str,
        body: Any = None,
        idempotency_key: str | None = None,
    ) -> Any:
        url  = f"{self._base_url}/api{path}"
        data = json.dumps(body).encode() if body is not None else None

        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "X-API-Key": self._api_key,
            "Accept": "application/json",
            "User-Agent": "achekconnect-python/2.0.0",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        last_exc: AchekConnectError | None = None

        for attempt in range(1, self._max_attempts + 1):
            req = Request(url, data=data, method=method, headers=headers)
            try:
                with urlopen(req, timeout=self._timeout) as resp:
                    return json.loads(resp.read())
            except HTTPError as exc:
                try:
                    payload: dict = json.loads(exc.read())
                except Exception:
                    payload = {}
                err = AchekConnectError(
                    payload.get("error", f"HTTP {exc.code}"),
                    status_code=exc.code,
                    code=payload.get("code"),
                )
                if exc.code not in _RETRYABLE_STATUSES or attempt >= self._max_attempts:
                    raise err from exc
                last_exc = err
            except URLError as exc:
                err = AchekConnectError(str(exc.reason), status_code=0)
                if attempt >= self._max_attempts:
                    raise err from exc
                last_exc = err

            # Exponential backoff: 0.5 s, 1.0 s, 2.0 s …
            time.sleep(self._initial_delay_s * (2 ** (attempt - 1)))

        raise last_exc or AchekConnectError("Max retries exceeded", status_code=0)

    def get(self, path: str) -> Any:
        return self._request("GET", path)

    def post(
        self,
        path: str,
        body: Any = None,
        idempotency_key: str | None = None,
    ) -> Any:
        return self._request("POST", path, body, idempotency_key)

    def patch(self, path: str, body: Any = None) -> Any:
        return self._request("PATCH", path, body)

    def put(self, path: str, body: Any = None) -> Any:
        return self._request("PUT", path, body)

    def delete(self, path: str) -> Any:
        return self._request("DELETE", path)
