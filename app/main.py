from functools import lru_cache
from logging import DEBUG, INFO, WARNING, basicConfig, getLogger
from typing import Union

from fastapi import FastAPI
from platform_services.keycloak import KeycloakWrapper
from platform_services.rabbitmq import RabbitMQWrapper
from platform_services.redis import RedisWrapper
from platform_services.sentry import SentryWrapper
from platform_services.service import PlatformService, get_general_settings
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from uvicorn import run

from app.routers.events_router import events_router
from app.routers.tasks_router import tasks_router

logger = getLogger(__name__)


def main() -> None:
    settings = get_general_settings()
    logger.info(f"Start {settings.title} {settings.version} http://{settings.host}:{settings.port}")
    logger.debug(f"Debug mode is {settings.debug}")
    basicConfig(
        level=DEBUG if settings.debug else INFO,
        format=settings.logger.format,
    )
    run(
        "app:create_app",
        host=settings.host,
        port=settings.port,
        log_level="debug" if settings.debug else "info",
        factory=True,
    )


def setup_logging() -> None:
    getLogger("aiormq").setLevel(WARNING)
    getLogger("aio_pika").setLevel(WARNING)


@lru_cache
def create_app() -> Union[FastAPI, SentryAsgiMiddleware]:
    setup_logging()

    service = PlatformService(
        SentryWrapper,
        RedisWrapper,
        KeycloakWrapper,
        RabbitMQWrapper,
    )
    service.app.include_router(events_router, prefix='/calendar'),
    service.app.include_router(tasks_router, prefix='/calendar')

    return service.runnable  # type: ignore
