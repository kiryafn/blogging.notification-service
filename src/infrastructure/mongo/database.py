from motor.motor_asyncio import AsyncIOMotorClient
from infrastructure.config import settings


class MongoDatabase:
    client: AsyncIOMotorClient = None

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        if cls.client is None:
            cls.client = AsyncIOMotorClient(settings.MONGO_URI)
        return cls.client

    @classmethod
    def close(cls):
        if cls.client:
            cls.client.close()