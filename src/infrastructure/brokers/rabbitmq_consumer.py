import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

import aio_pika
from aio_pika import RobustConnection
from aio_pika.abc import AbstractIncomingMessage

from domain.entities import ResetPasswordMessage
from infrastructure.config import settings


logger = logging.getLogger(__name__)


def build_reset_password_email(payload: dict[str, Any]) -> ResetPasswordMessage:
    """Build ResetPasswordMessage from event payload."""
    recipient_email = payload["recipient_email"]
    username = payload.get("username", "User")
    reset_link = payload["reset_link"]

    body = (
        f"Hello {username},\n\n"
        f"You requested a password reset. Click the link below to reset your password:\n\n"
        f"{reset_link}\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"This link will expire in 24 hours."
    )

    return ResetPasswordMessage(
        message_id=uuid.uuid4(),
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),  # Not provided by event
        email=recipient_email,
        subject="Password Reset Request",
        body=body,
        published_at=datetime.now(timezone.utc),
        template_context={"username": username, "reset_link": reset_link},
    )


async def process_reset_password_message(
    message: AbstractIncomingMessage,
    handler: Callable[[ResetPasswordMessage], Awaitable[None]],
) -> None:
    """Parse message and invoke handler. Rejects/nacks on invalid format."""
    async with message.process(ignore_processed=True):
        try:
            body = json.loads(message.body.decode())
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error("Invalid message body (not JSON): %s", e)
            await message.reject(requeue=False)
            return

        event_type = body.get("event_type")
        payload = body.get("payload")

        if event_type != "password_reset_requested" or not payload:
            logger.warning("Unknown event_type or missing payload: %s", body)
            await message.reject(requeue=False)
            return

        required = ("recipient_email", "reset_link")
        if not all(payload.get(k) for k in required):
            logger.warning("Missing required payload fields: %s", payload)
            await message.reject(requeue=False)
            return

        try:
            reset_msg = build_reset_password_email(payload)
            await handler(reset_msg)
            logger.info("Processed password_reset_requested for %s", reset_msg.email)
        except Exception as e:
            logger.exception("Failed to process reset password message: %s", e)
            await message.reject(requeue=True)


async def consume_reset_password_queue(
    connection: RobustConnection,
    handler: Callable[[ResetPasswordMessage], Awaitable[None]],
) -> None:
    """Start consuming from reset-password-stream queue."""
    async with connection.channel() as channel:
        await channel.set_qos(prefetch_count=1)

        queue = await channel.declare_queue(
            settings.RABBITMQ_QUEUE_NAME,
            durable=True,
        )

        logger.info("Consuming from queue: %s", settings.RABBITMQ_QUEUE_NAME)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await process_reset_password_message(message, handler)
