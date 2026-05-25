from __future__ import annotations

from .http import HttpClient
from .modules import OtpModule, AlertsModule, TicketsModule, BroadcastsModule, EmailModule
from .webhooks import AchekWebhookHelper


class AchekConnect:
    """
    Achek Connect Python SDK client.

    Args:
        api_key:          Your Achek Connect API key (starts with ``achek_``)
        base_url:         Override the API base URL
                          (default: ``https://api.achek.com.ng``)
        timeout:          Request timeout in seconds (default: 15)
        max_attempts:     Total attempts per request including the first try.
                          Retries use exponential back-off. (default: 3)
        initial_delay_ms: Initial retry delay in milliseconds (default: 500)

    Example::

        from achek import AchekConnect

        client = AchekConnect(api_key="achek_live_xxxxxxxxxxxx")

        # Send OTP
        result     = client.otp.send("+2348XXXXXXXXX")
        request_id = result["requestId"]

        # Verify OTP
        if client.otp.verify(request_id, user_code)["valid"]:
            login_user()

        # Transaction alert
        client.alerts.transaction(
            "+2348XXXXXXXXX",
            type="credit",
            amount=50_000,
            reference="TXN-9988",
            account_name="Chidi Okeke",
            balance=180_000,
        )

        # Verify an incoming webhook
        helper = AchekWebhookHelper("your_webhook_secret")
        if helper.verify(sig_header, raw_body):
            event = helper.parse(raw_body)
    """

    #: OTP sending and verification
    otp: OtpModule
    #: Custom alerts and transaction notifications
    alerts: AlertsModule
    #: Support ticket management with WhatsApp updates
    tickets: TicketsModule
    #: Broadcast messages to multiple recipients
    broadcasts: BroadcastsModule
    #: Transactional email delivery
    email: EmailModule

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.achek.com.ng",
        timeout: int = 15,
        max_attempts: int = 3,
        initial_delay_ms: int = 500,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        http = HttpClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_attempts=max_attempts,
            initial_delay_ms=initial_delay_ms,
        )
        self.otp        = OtpModule(http)
        self.alerts     = AlertsModule(http)
        self.tickets    = TicketsModule(http)
        self.broadcasts = BroadcastsModule(http)
        self.email      = EmailModule(http)
