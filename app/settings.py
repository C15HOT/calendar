import os
from functools import lru_cache
from logging import getLogger

from dotenv import load_dotenv
from platform_services.wrapper_base import ServiceSettingsBase


logger = getLogger("settings")

class PostgresSettings(ServiceSettingsBase):


    avatar_postgres_server: str = os.getenv('avatar_postgres_server')
    avatar_postgres_db: str = os.getenv('avatar_postgres_db')

class RabbitMQEntitiesSubSettings(ServiceSettingsBase):
    ...


class Settings(ServiceSettingsBase):
    rmq: RabbitMQEntitiesSubSettings = RabbitMQEntitiesSubSettings()
    postgres_settings: PostgresSettings = PostgresSettings()



@lru_cache()
def get_settings() -> Settings:
    logger.info("Settings created")
    settings = Settings()
    print(settings.postgres_settings.avatar_postgres_server)
    return settings
