from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # MongoDB
    MONGO_URI: str
    MONGO_DB_NAME: str = "notification_db"
    MONGO_COLLECTION: str = "messages"

    # RabbitMQ
    RABBITMQ_URI: str
    RABBITMQ_QUEUE_NAME: str = "reset-password-stream"
    RABBITMQ_DLQ_NAME: str = "reset-password-dlq"

    # AWS
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_SES_SENDER: str

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()