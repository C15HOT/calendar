import os
from functools import lru_cache
from logging import getLogger
from platform_services.wrapper_base import ServiceSettingsBase

logger = getLogger("settings")

class PostgresSettings(ServiceSettingsBase):


    postgres_server: str
    postgres_db: str



class RabbitMQEntitiesSubSettings(ServiceSettingsBase):
    ...


class Settings(ServiceSettingsBase):
    rmq: RabbitMQEntitiesSubSettings = RabbitMQEntitiesSubSettings()
    postgres_settings: PostgresSettings = PostgresSettings()



@lru_cache()
def get_settings() -> Settings:
    logger.info("Settings created")
    settings = Settings()
    return settings
