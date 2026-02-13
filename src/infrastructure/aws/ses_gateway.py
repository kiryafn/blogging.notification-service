import aioboto3
from botocore.exceptions import ClientError

from application.ports.services.email_gateway import EmailGateway
from domain.entities import ResetPasswordMessage
from domain.exceptions import EmailSendingFailedError
from infrastructure.config import settings


class SesEmailGateway(EmailGateway):
    def __init__(self):
        self.session = aioboto3.Session()

    async def send_email(self, message: ResetPasswordMessage) -> None:
        try:
            async with self.session.client(
                "ses",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            ) as client:
                await client.send_email(
                    Source=settings.AWS_SES_SENDER,
                    Destination={"ToAddresses": [message.email]},
                    Message={
                        "Subject": {"Data": message.subject, "Charset": "UTF-8"},
                        "Body": {
                            "Text": {"Data": message.body, "Charset": "UTF-8"},
                        },
                    },
                )
        except ClientError as e:
            raise EmailSendingFailedError(f"Failed to send email via SES: {str(e)}")