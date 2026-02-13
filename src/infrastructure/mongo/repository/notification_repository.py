from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession
from pymongo import ReturnDocument

from application.ports.repositories import NotificationRepository
from infrastructure.config import settings
from domain.entities import ResetPasswordMessage


class MongoNotificationRepository(NotificationRepository):
    def __init__(self, client: AsyncIOMotorClient):
        self.client = client
        self.db = self.client[settings.MONGO_DB_NAME]
        self.collection = self.db[settings.MONGO_COLLECTION]

    async def save(
        self,
        message: ResetPasswordMessage,
        session: AsyncIOMotorClientSession | None = None,
    ) -> None:
        document = message.model_dump(mode="json")
        document["_id"] = str(message.message_id)
        document["user_id"] = str(message.user_id)

        await self.collection.insert_one(document, session=session)

    async def mark_as_sent(
        self, message_id: str, session: AsyncIOMotorClientSession | None = None
    ) -> None:
        await self.collection.find_one_and_update(
            {"_id": message_id},
            {
                "$set": {"sent_at": datetime.now(timezone.utc)},
            },
            session=session,
            return_document=ReturnDocument.AFTER,
        )
