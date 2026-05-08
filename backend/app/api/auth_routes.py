"""Auth endpoints: signup, login, me."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.deps import CurrentUser, DbDep
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    SignupRequest,
    TokenResponse,
    UserPublic,
)

log = logging.getLogger("citracker.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_public(user: User) -> UserPublic:
    return UserPublic(id=user.id, email=user.email, name=user.name)


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(req: SignupRequest, db: DbDep) -> TokenResponse:
    email = req.email.lower().strip()
    try:
        existing = await db.scalar(select(User).where(User.email == email))
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        user = User(
            email=email,
            password_hash=hash_password(req.password),
            name=(req.name or "").strip() or None,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    except HTTPException:
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    except SQLAlchemyError as exc:
        await db.rollback()
        log.exception("signup db error")
        raise HTTPException(
            status_code=500,
            detail=f"Database error during signup: {type(exc).__name__}",
        ) from exc

    return TokenResponse(
        access_token=create_access_token(user.id),
        user=_to_public(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: DbDep) -> TokenResponse:
    email = req.email.lower().strip()
    try:
        user = await db.scalar(select(User).where(User.email == email))
    except SQLAlchemyError as exc:
        log.exception("login db error")
        raise HTTPException(
            status_code=500,
            detail=f"Database error during login: {type(exc).__name__}",
        ) from exc

    if user is None or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return TokenResponse(
        access_token=create_access_token(user.id),
        user=_to_public(user),
    )


@router.get("/me", response_model=UserPublic)
async def me(user: CurrentUser) -> UserPublic:
    return _to_public(user)
