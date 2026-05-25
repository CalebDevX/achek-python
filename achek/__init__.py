"""
achek — Official Python SDK for Achek Connect

WhatsApp OTP verification, automated alerts, transaction notifications,
transactional email, ticket tracking, and webhook utilities for
Nigerian developers.

pip install achek

Usage::

    from achek import AchekConnect, AchekWebhookHelper

    client = AchekConnect(api_key="achek_live_xxxxxxxxxxxx")

    # Send OTP
    result     = client.otp.send("+2348XXXXXXXXX")
    request_id = result["requestId"]

    # Verify OTP
    verification = client.otp.verify(request_id, user_code)
    if verification["valid"]:
        print("User verified!")

    # Verify incoming webhook
    helper = AchekWebhookHelper("your_webhook_secret")
    if helper.verify(sig_header, raw_body):
        event = helper.parse(raw_body)
"""

from .client    import AchekConnect
from .exceptions import AchekConnectError
from .webhooks  import AchekWebhookHelper

__all__    = ["AchekConnect", "AchekConnectError", "AchekWebhookHelper"]
__version__ = "2.0.0"
