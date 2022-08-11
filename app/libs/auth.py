import logging

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from platform_services.keycloak.injectors import JWTTokenModel, strict_bearer_auth
from pydantic import UUID4

logger = logging.getLogger(__name__)


async def auth_required(token: JWTTokenModel = Depends(strict_bearer_auth)) -> UUID4:
    try:
        return token.subject
    except ValueError as err:
        logger.error(f"Invalid subject in JTW: {token.json()}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentails",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err
