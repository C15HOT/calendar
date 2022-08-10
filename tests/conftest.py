import asyncio
import logging
from typing import Any, AsyncGenerator, Callable, Dict, Generator, TypeVar
from unittest.mock import patch

import pytest
from _pytest.monkeypatch import MonkeyPatch
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient
from jose import jwt

from app.main import create_app
from app.settings import get_settings

logger = logging.getLogger("tests")
settings = get_settings()

PyTestFixture = TypeVar("PyTestFixture", bound=Callable[..., object])


@pytest.fixture(
    name="client_sso_id",
    scope="session",
)
def client_sso_id_fixture() -> str:
    return "01234567-89ab-cdef-0123-456789abcdef"


@pytest.fixture(
    name="event_loop",
    scope="session",
)
def event_loop_fixture() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(
    name="monkeypatch_session",
    scope="session",
)
def monkeypatch_session_fixture():
    monkey_patcher = MonkeyPatch()
    yield monkey_patcher
    monkey_patcher.undo()


@pytest.fixture(
    scope="function",
    autouse=True,
)
def logs_config(caplog: PyTestFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="tests")
    caplog.set_level(logging.WARNING, logger="httpx")


@pytest.mark.asyncio
@pytest.fixture(
    name="patch_external_services",
    scope="session",
)
async def patch_external_services_fixture(
    monkeypatch_session,  # pylint: disable=unused-argument
) -> None:
    ...


@pytest.fixture(
    name="app",
    scope="session",
)
def app_fixture(
    event_loop: asyncio.AbstractEventLoop,  # pylint: disable=unused-argument
    patch_external_services: PyTestFixture,  # pylint: disable=unused-argument
) -> FastAPI:
    with patch("keycloak.KeycloakOpenID.public_key") as mocked_pub_key:
        mocked_pub_key.return_value = "public-key"
        yield create_app()  # type: ignore


@pytest.fixture(
    name="auth_headers",
    scope="session",
)
def auth_headers_fixture(
    client_sso_id: PyTestFixture,
) -> Dict[str, Any]:
    token = jwt.encode(
        claims=dict(sub=client_sso_id, preferred_username="test"),
        key="invalid-key",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
@pytest.fixture(
    name="app_lifespan",
    scope="session",
)
async def app_lifespan_fixture(
    app: FastAPI,
    event_loop: asyncio.AbstractEventLoop,  # pylint: disable=unused-argument
) -> AsyncGenerator[AsyncClient, None]:
    async with LifespanManager(app, startup_timeout=60, shutdown_timeout=60):
        yield app


@pytest.mark.asyncio
@pytest.fixture(
    name="client",
    scope="session",
)
async def client_fixture(
    app_lifespan: FastAPI,
    auth_headers: PyTestFixture,
) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app_lifespan, base_url="http://platform_service", headers=auth_headers) as test_client:
        yield test_client


