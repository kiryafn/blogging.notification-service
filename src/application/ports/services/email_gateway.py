from abc import ABC

from domain.entities import ResetPasswordMessage


class EmailGateway(ABC):
    async def send_email(self, message: ResetPasswordMessage) -> None:
        pass