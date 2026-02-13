from pathlib import Path

import aioboto3
from botocore.exceptions import ClientError
from jinja2 import Environment, FileSystemLoader, select_autoescape

from application.ports.services.email_gateway import EmailGateway
from domain.entities import ResetPasswordMessage
from domain.exceptions import EmailSendingFailedError
from infrastructure.config import settings


def _get_templates_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "templates"


class SesEmailGateway(EmailGateway):
    TEMPLATE_NAME = "reset_password.html"

    def __init__(self) -> None:
        self.session = aioboto3.Session()
        templates_dir = _get_templates_dir()
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html"]),
        )

    def _render_html(self, message: ResetPasswordMessage) -> str:
        template = self._env.get_template(self.TEMPLATE_NAME)
        return template.render(**message.template_context)

    async def send_email(self, message: ResetPasswordMessage) -> None:
        html_body = self._render_html(message) if message.template_context else message.body

        try:
            async with self.session.client(
                "ses",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            ) as client:
                await client.send_email(
                    Source=settings.AWS_SES_SENDER,
                    Destination={"ToAddresses": [str(message.email)]},
                    Message={
                        "Subject": {"Data": message.subject, "Charset": "UTF-8"},
                        "Body": {
                            "Text": {"Data": message.body, "Charset": "UTF-8"},
                            "Html": {"Data": html_body, "Charset": "UTF-8"},
                        },
                    },
                )
        except ClientError as e:
            raise EmailSendingFailedError(f"Failed to send email via SES: {str(e)}")
