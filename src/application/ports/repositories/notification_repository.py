from abc import ABC
from domain.entities.reset_password_message import ResetPasswordMessage

class NotificationRepository(ABC):
    async def save(self, message: ResetPasswordMessage) -> None:
        pass

    async def mark_as_sent(self, message_id: str) -> None:
        pass