"""Shared FastAPI dependencies: DB session + current-user resolver."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_optional_user(
    db: DbDep,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User | None:
    """Return user if authenticated, None otherwise."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except Exception:
        return None

    user = await db.get(User, user_id)
    return user


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


async def get_required_user(
    db: DbDep,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    """Require authentication, raise 401 if not authenticated."""
    from fastapi import HTTPException, status

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user


CurrentUser = Annotated[User, Depends(get_required_user)]