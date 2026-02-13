import asyncio
import logging
import signal
import sys

import aio_pika

from domain.entities import ResetPasswordMessage
from infrastructure.aws.ses_gateway import SesEmailGateway
from infrastructure.brokers.rabbitmq_consumer import consume_reset_password_queue
from infrastructure.config import settings


logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

_connection: aio_pika.RobustConnection | None = None


async def handle_reset_password(message: ResetPasswordMessage) -> None:
    """Send password reset email via SES."""
    gateway = SesEmailGateway()
    await gateway.send_email(message)


async def run_consumer() -> None:
    global _connection
    _connection = await aio_pika.connect_robust(
        settings.RABBITMQ_URI,
        timeout=30,
    )
    logger.info("Connected to RabbitMQ")

    try:
        await consume_reset_password_queue(_connection, handle_reset_password)
    finally:
        if _connection:
            await _connection.close()
            logger.info("RabbitMQ connection closed")


def main() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def shutdown(_sig=None, _frame=None):
        logger.info("Shutting down...")
        if _connection and not _connection.is_closed:
            loop.call_soon_threadsafe(lambda: asyncio.ensure_future(_connection.close()))

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, shutdown)

    try:
        loop.run_until_complete(run_consumer())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()


if __name__ == "__main__":
    main()
