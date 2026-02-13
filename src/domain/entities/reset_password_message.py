import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class ResetPasswordMessage(BaseModel):
    message_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    email: EmailStr
    subject: str
    body: str
    published_at: datetime
    sent_at: Optional[datetime] = None
    template_context: dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = True