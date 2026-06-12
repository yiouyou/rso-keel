"""Checkpointer factory.

Returns a LangGraph checkpointer appropriate for the environment:
  - No URL → MemorySaver  (tests, local dev, standalone usage)
  - postgres_url given → AsyncPostgresSaver (production, crash-safe persistence)

Two entry points:
  make_checkpointer(postgres_url)     — sync, returns MemorySaver only
  async_checkpointer_ctx(postgres_url) — async context manager, returns
                                          MemorySaver or AsyncPostgresSaver

keel ships only the factory; the concrete PostgresSaver import is deferred so
that langgraph-checkpoint-postgres is not a hard dependency of the package.
The RSO platform layer calls async_checkpointer_ctx(settings.database_url).
"""

from __future__ import annotations

import contextlib
import re
from typing import Any, AsyncIterator


def _to_psycopg_url(url: str) -> str:
    """Convert SQLAlchemy async URL to a plain psycopg3 connection string.

    PostgresSaver uses psycopg3, which expects 'postgresql://...'
    RSO uses asyncpg driver: 'postgresql+asyncpg://...'
    """
    return re.sub(r"\+asyncpg", "", url, count=1)


def make_checkpointer(postgres_url: str | None = None) -> Any:
    """Return a LangGraph MemorySaver (sync, in-process only).

    For production use with Postgres, prefer async_checkpointer_ctx().
    This function is kept for backward compatibility with sync test paths.
    """
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()


@contextlib.asynccontextmanager
async def async_checkpointer_ctx(postgres_url: str | None = None) -> AsyncIterator[Any]:
    """Async context manager yielding a LangGraph checkpointer.

    Yields:
        MemorySaver  — when postgres_url is None (tests, local dev)
        AsyncPostgresSaver — when postgres_url is provided (production)

    Usage:
        async with async_checkpointer_ctx(settings.database_url) as cp:
            compiled = keel_compile(ir, checkpointer=cp)
            result = await compiled.ainvoke(state, config=cfg)
    """
    if not postgres_url:
        from langgraph.checkpoint.memory import MemorySaver
        yield MemorySaver()
        return

    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    except ImportError as exc:
        raise RuntimeError(
            "AsyncPostgresSaver requires 'langgraph-checkpoint-postgres'. "
            "Install it with: pip install langgraph-checkpoint-postgres"
        ) from exc

    conn_string = _to_psycopg_url(postgres_url)
    async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
        await checkpointer.setup()
        yield checkpointer
