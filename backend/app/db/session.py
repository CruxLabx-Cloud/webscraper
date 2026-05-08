"""Async SQLAlchemy session and engine.

Supports both Postgres (asyncpg) for prod/docker and SQLite (aiosqlite) for
zero-config local dev. Tables are created at startup via Base.metadata.create_all.

If startup detects a SQLite DB whose existing schema is missing columns we
just added in code (a common dev-mode footgun that breaks signup/login with
opaque OperationalErrors), we auto-migrate by adding the missing columns.
"""
from __future__ import annotations

import logging
from typing import AsyncIterator

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

log = logging.getLogger("citracker.db")


class Base(DeclarativeBase):
    pass


_engine_kwargs: dict = {"future": True, "echo": False}
if settings.database_url.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.database_url, **_engine_kwargs)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create missing tables and (sqlite only) add missing columns in-place."""
    from app import models  # noqa: F401  — register models with Base.metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Best-effort additive migration for SQLite dev DBs only.
        if settings.database_url.startswith("sqlite"):
            await conn.run_sync(_sqlite_add_missing_columns)


def _sqlite_add_missing_columns(sync_conn) -> None:
    """For each declared model table, ALTER TABLE ADD COLUMN for any missing column.

    SQLite supports ADD COLUMN for nullable / default-bearing columns, which
    covers all of the columns we add over time in this project. Anything more
    complex (NOT NULL without default) is skipped with a warning.
    """
    inspector = inspect(sync_conn)
    existing_tables = set(inspector.get_table_names())
    for table_name, table in Base.metadata.tables.items():
        if table_name not in existing_tables:
            continue
        existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
        for col in table.columns:
            if col.name in existing_cols:
                continue
            try:
                col_type = col.type.compile(dialect=sync_conn.dialect)
                default_clause = ""
                if col.default is not None and getattr(col.default, "arg", None) is not None:
                    val = col.default.arg
                    if isinstance(val, bool):
                        default_clause = f" DEFAULT {1 if val else 0}"
                    elif isinstance(val, (int, float)):
                        default_clause = f" DEFAULT {val}"
                    elif isinstance(val, str):
                        default_clause = f" DEFAULT '{val}'"
                null_clause = "" if col.nullable else " NOT NULL"
                if not col.nullable and not default_clause:
                    log.warning(
                        "skip ADD COLUMN %s.%s (NOT NULL no default — migrate manually)",
                        table_name,
                        col.name,
                    )
                    continue
                sql = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{default_clause}{null_clause}"
                log.info("auto-migrating: %s", sql)
                sync_conn.execute(text(sql))
            except Exception as exc:  # noqa: BLE001
                log.warning("ADD COLUMN failed for %s.%s: %s", table_name, col.name, exc)
