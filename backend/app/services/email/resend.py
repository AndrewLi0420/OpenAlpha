from __future__ import annotations

from dataclasses import dataclass

import resend
from resend.emails._emails import Emails

from app.core.logger import logger
from .errors import SendEmailError


@dataclass
class ResendProvider:
    """Resend email provider implementation"""
    api_key: str

    def __post_init__(self):
        """Set the Resend API key globally for the resend module"""
        resend.api_key = self.api_key

    async def send_email(
        self,
        *,
        recipient: tuple[str, str | None],
        sender: tuple[str, str | None],
        subject: str,
        text: str | None = None,
        html: str | None = None,
    ):
        """Send email via Resend API
        
        Resend API documentation: https://resend.com/docs/api-reference/emails/send-email
        """
        from_email, from_name = sender
        to_email, to_name = recipient
        
        # Resend API expects a "from" field in format "Name <email>" or just "email"
        from_address = f"{from_name} <{from_email}>" if from_name else from_email
        
        # Build "to" field - Resend accepts string or list
        to_address = f"{to_name} <{to_email}>" if to_name else to_email
        
        try:
            # Prepare email params according to Resend API
            params = {
                "from": from_address,
                "to": to_address,
                "subject": subject,
            }
            
            # Add text or html content (both can be provided)
            if html:
                params["html"] = html
            if text:
                params["text"] = text
            
            # Send email via Resend API
            # Note: Emails.send() is synchronous, but we're in an async context
            # We'll run it in a thread pool to avoid blocking
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: Emails.send(params)
            )
            
            # Resend returns a response with id field
            message_id = response.get("id") if isinstance(response, dict) else str(response)
            logger.info(f"Resend email sent successfully. Message ID: {message_id}")
            
        except Exception as e:
            logger.error(f"Failed to send email via Resend: {e}")
            raise SendEmailError(f"Resend API error: {str(e)}") from e

