"""
Webhook signature verification and parsing for Achek Connect.

Achek signs every webhook delivery with HMAC-SHA256 using your webhook secret.
The signature is sent in the ``X-Achek-Signature`` HTTP header as
``sha256=<hex-digest>``.

Usage (Flask example)::

    from flask import Flask, request, abort
    from achek import AchekWebhookHelper

    app = Flask(__name__)
    helper = AchekWebhookHelper("your_webhook_secret")

    @app.post("/webhook")
    def webhook():
        sig = request.headers.get("X-Achek-Signature", "")
        if not helper.verify(sig, request.get_data()):
            abort(400, "Invalid signature")
        event = helper.parse(request.get_data())
        print(event["event"])  # e.g. "otp.verified", "handoff.requested"
        return "", 200

Usage (Django example)::

    from django.views.decorators.csrf import csrf_exempt
    from django.http import HttpResponse, HttpResponseBadRequest
    from achek import AchekWebhookHelper

    helper = AchekWebhookHelper("your_webhook_secret")

    @csrf_exempt
    def webhook(request):
        sig = request.headers.get("X-Achek-Signature", "")
        if not helper.verify(sig, request.body):
            return HttpResponseBadRequest("Invalid signature")
        event = helper.parse(request.body)
        return HttpResponse(status=200)
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


class AchekWebhookHelper:
    """
    Verify and parse incoming Achek webhook events.

    Args:
        webhook_secret: The webhook secret shown in your Achek dashboard.
    """

    def __init__(self, webhook_secret: str) -> None:
        if not webhook_secret:
            raise ValueError("webhook_secret is required")
        self._secret = webhook_secret.encode()

    def verify(self, signature: str, payload: bytes | str) -> bool:
        """
        Verify the HMAC-SHA256 signature from the ``X-Achek-Signature`` header.

        Uses :func:`hmac.compare_digest` to prevent timing attacks.

        Args:
            signature: Value of the ``X-Achek-Signature`` header
                       (e.g. ``"sha256=abc123..."``).
            payload:   Raw request body as bytes or str.

        Returns:
            ``True`` if the signature is valid, ``False`` otherwise.
        """
        try:
            raw = payload if isinstance(payload, bytes) else payload.encode()
            expected = hmac.new(self._secret, raw, hashlib.sha256).hexdigest()
            sig = signature.removeprefix("sha256=")
            return hmac.compare_digest(sig, expected)
        except Exception:
            return False

    def parse(self, payload: bytes | str) -> dict[str, Any]:
        """
        Decode and return the webhook event as a dict.

        Args:
            payload: Raw request body as bytes or str.

        Returns:
            Parsed event dict with at least ``event`` and ``timestamp`` keys.
        """
        raw = payload if isinstance(payload, str) else payload.decode()
        return json.loads(raw)
