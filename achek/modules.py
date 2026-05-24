from __future__ import annotations

from typing import Any, Literal
from urllib.parse import urlencode

from .http import HttpClient


class OtpModule:
    """Send and verify WhatsApp OTPs."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def send(
        self,
        phone_number: str,
        *,
        template: str | None = None,
        recipient_name: str | None = None,
        company_name: str | None = None,
        sender_number_id: int | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        """
        Send a WhatsApp OTP to a phone number.

        Returns a dict with ``requestId`` and ``expiresAt``.
        Store ``requestId`` — you'll need it to verify the code.

        Args:
            phone_number:     E.164 format, e.g. ``"+2348XXXXXXXXX"``
            template:         Custom message with ``{{code}}`` placeholder
                              (Growth+ plans only)
            recipient_name:   Replaces ``{{name}}`` in template
            company_name:     Replaces ``{{company}}`` in template
            sender_number_id: Specific WhatsApp number ID to send from
            idempotency_key:  Reuse to safely retry without double-sending

        Example::

            result     = client.otp.send("+2348XXXXXXXXX")
            request_id = result["requestId"]
        """
        body: dict = {"phoneNumber": phone_number}
        if template:
            body["template"] = template
        if recipient_name:
            body["recipientName"] = recipient_name
        if company_name:
            body["companyName"] = company_name
        if sender_number_id is not None:
            body["senderNumberId"] = sender_number_id
        return self._http.post("/otp/send", body, idempotency_key)

    def verify(self, request_id: str, code: str) -> dict:
        """
        Verify the OTP code entered by the user.

        Returns ``{"valid": True}`` on success.

        Args:
            request_id: The requestId returned by :meth:`send`
            code:       The 6-digit code entered by the user

        Example::

            result = client.otp.verify(request_id, "847293")
            if result["valid"]:
                login_user()
        """
        return self._http.post("/otp/verify", {"requestId": request_id, "code": code})

    def logs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: Literal["sent", "verified", "failed", "expired"] | None = None,
    ) -> list[dict]:
        """Fetch your OTP delivery logs."""
        params: dict = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        return self._http.get(f"/otp/logs?{urlencode(params)}")


class AlertsModule:
    """Send custom WhatsApp alerts and transaction notifications."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def send(
        self,
        phone_number: str,
        message: str,
        *,
        ticket_id: str | None = None,
        transaction_ref: str | None = None,
        category: Literal["alert", "transaction", "notification"] = "alert",
        idempotency_key: str | None = None,
    ) -> dict:
        """
        Send a custom WhatsApp message to any phone number.

        Args:
            phone_number:    E.164 format e.g. ``"+2348XXXXXXXXX"``
            message:         Plain text or WhatsApp markdown (``*bold*``, ``_italic_``)
            ticket_id:       Link this alert to a ticket
            transaction_ref: Transaction reference for tracking
            category:        Alert category for logging
            idempotency_key: Reuse to safely retry without double-sending

        Example::

            client.alerts.send(
                "+2348XXXXXXXXX",
                "*Your account has been credited with ₦5,000*",
            )
        """
        body: dict = {
            "phoneNumber": phone_number,
            "message": message,
            "category": category,
        }
        if ticket_id:
            body["ticketId"] = ticket_id
        if transaction_ref:
            body["transactionRef"] = transaction_ref
        return self._http.post("/alerts/send", body, idempotency_key)

    def transaction(
        self,
        phone_number: str,
        *,
        type: Literal["credit", "debit", "transfer", "reversal"] | str,
        amount: float,
        reference: str,
        currency: str = "NGN",
        account_name: str | None = None,
        balance: float | None = None,
        description: str | None = None,
    ) -> dict:
        """
        Send a formatted transaction alert via WhatsApp.

        Automatically builds a clear, branded WhatsApp message with emoji
        labels, bold amounts, and running balance.

        Example::

            client.alerts.transaction(
                "+2348XXXXXXXXX",
                type="debit",
                amount=15000,
                reference="TXN-001",
                account_name="Emeka Okafor",
                balance=240000,
                description="Transfer to Kuda",
            )
        """
        symbol = "₦" if currency == "NGN" else f"{currency} "
        labels = {
            "credit":   "💰 Credit Alert",
            "debit":    "💸 Debit Alert",
            "transfer": "🔄 Transfer Alert",
            "reversal": "↩️ Reversal Alert",
        }
        label = labels.get(type, f"📋 {type.title()} Alert")

        def fmt(n: float) -> str:
            return f"{n:,.2f}"

        lines = [f"*{label}*", ""]
        lines.append(f"Amount: *{symbol}{fmt(amount)}*")
        if account_name:
            lines.append(f"Account: {account_name}")
        lines.append(f"Ref: `{reference}`")
        if description:
            lines.append(f"Narration: {description}")
        if balance is not None:
            lines.append(f"Balance: *{symbol}{fmt(balance)}*")
        lines += ["", "_Powered by Achek Connect_"]

        return self.send(
            phone_number,
            "\n".join(lines),
            transaction_ref=reference,
            category="transaction",
        )


class TicketsModule:
    """Manage support tickets with WhatsApp customer updates."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        phone_number: str,
        subject: str,
        *,
        description: str | None = None,
        priority: Literal["low", "normal", "high", "urgent"] = "normal",
        metadata: dict | None = None,
        notify_customer: bool = True,
        notification_message: str | None = None,
    ) -> dict:
        """
        Create a support ticket and optionally notify the customer on WhatsApp.

        Example::

            ticket    = client.tickets.create(
                "+2348XXXXXXXXX",
                "Payment not reflecting",
                description="Paid ₦5,000 but order not updated",
                priority="high",
                notify_customer=True,
            )
            ticket_id = ticket["ticketId"]
        """
        body: dict = {
            "phoneNumber": phone_number,
            "subject": subject,
            "priority": priority,
            "notifyCustomer": notify_customer,
        }
        if description:
            body["description"] = description
        if metadata:
            body["metadata"] = metadata
        if notification_message:
            body["notificationMessage"] = notification_message
        return self._http.post("/tickets", body)

    def list(
        self,
        *,
        status: Literal["open", "in_progress", "resolved", "closed"] | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """List all tickets."""
        params: dict = {"limit": limit}
        if status:
            params["status"] = status
        return self._http.get(f"/tickets?{urlencode(params)}")

    def get(self, ticket_id: str) -> dict:
        """Get a ticket by ID."""
        return self._http.get(f"/tickets/{ticket_id}")

    def update(
        self,
        ticket_id: str,
        *,
        status: Literal["open", "in_progress", "resolved", "closed"] | None = None,
        priority: Literal["low", "normal", "high", "urgent"] | None = None,
        notify_customer: bool = False,
        notification_message: str | None = None,
    ) -> dict:
        """Update a ticket's status or priority."""
        body: dict = {"notifyCustomer": notify_customer}
        if status:
            body["status"] = status
        if priority:
            body["priority"] = priority
        if notification_message:
            body["notificationMessage"] = notification_message
        return self._http.patch(f"/tickets/{ticket_id}", body)

    def resolve(self, ticket_id: str, message: str | None = None) -> dict:
        """Resolve a ticket and notify the customer."""
        return self.update(
            ticket_id,
            status="resolved",
            notify_customer=True,
            notification_message=message,
        )


class BroadcastsModule:
    """Send WhatsApp broadcasts to multiple recipients."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def send(self, name: str, message: str, recipients: list[str]) -> dict:
        """
        Send a broadcast message to up to 1,000 phone numbers.

        Args:
            name:       Display name for this broadcast
            message:    WhatsApp markdown supported (``*bold*``, ``_italic_``)
            recipients: List of E.164 phone numbers

        Example::

            client.broadcasts.send(
                name="Black Friday Promo",
                message="🔥 *50% OFF* today only! Use code: *FRIDAY50*",
                recipients=["+2348XXXXXXXXX", "+2348YYYYYYYYY"],
            )
        """
        return self._http.post("/broadcasts", {
            "name": name,
            "message": message,
            "recipients": recipients,
        })

    def list(self) -> list[dict]:
        """List recent broadcasts."""
        return self._http.get("/broadcasts")

    def status(self, broadcast_id: int) -> dict:
        """Get the delivery status of a broadcast."""
        return self._http.get(f"/broadcasts/{broadcast_id}")


class EmailModule:
    """Send transactional emails via Achek's configured SMTP."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def send(
        self,
        to: str,
        subject: str,
        *,
        text: str | None = None,
        html: str | None = None,
        from_name: str | None = None,
    ) -> dict:
        """
        Send a transactional email.

        The sender address and domain are configured in your Achek dashboard.
        Supply either ``text`` or ``html`` (or both; ``html`` takes precedence
        in mail clients that support it).

        Args:
            to:        Recipient email address
            subject:   Email subject line
            text:      Plain-text body
            html:      HTML body (takes precedence over text)
            from_name: Sender display name override

        Example::

            client.email.send(
                to="customer@example.com",
                subject="Your OTP",
                html="<p>Your code is <strong>847293</strong>. Valid for 10 minutes.</p>",
            )
        """
        body: dict[str, Any] = {"to": to, "subject": subject}
        if text:
            body["text"] = text
        if html:
            body["html"] = html
        if from_name:
            body["fromName"] = from_name
        return self._http.post("/email/send", body)
