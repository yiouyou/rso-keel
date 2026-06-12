"""Idempotent content-hash cache for expensive graph-external steps.

Used when a handler performs work that is:
  - expensive (LLM call, file import, OSS upload/download)
  - outside the LangGraph node boundary (so LangGraph's checkpoint alone
    cannot deduplicate it on resume)

Usage pattern:
    result, was_cached = cache.get_or_run(inputs, fn)
    if was_cached:
        # LLM was NOT called again — cost is zero
        ...

The cache key is SHA-256 of the canonical JSON serialisation of *inputs*.
Implementations swap the backend (InMemoryCache for tests, Redis/DB in prod).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Protocol, runtime_checkable


@runtime_checkable
class CacheBackend(Protocol):
    """Storage contract for the idempotent cache."""

    def get(self, key: str) -> dict[str, Any] | None: ...
    def set(self, key: str, value: dict[str, Any]) -> None: ...


class InMemoryCache:
    """In-process cache backend — for tests and standalone usage."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        return self._store.get(key)

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._store[key] = value

    def __len__(self) -> int:
        return len(self._store)


def _cache_key(inputs: dict[str, Any]) -> str:
    canonical = json.dumps(inputs, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


class ContentHashCache:
    """Wrap a CacheBackend with content-hash keying.

    get_or_run(inputs, fn) → (result, was_cached)
      - If key exists in backend: return cached result, True
      - Otherwise: call fn(), store result, return result, False

    The caller uses *was_cached* to distinguish "LLM was called" from
    "result was replayed from cache" — enabling zero-cost crash recovery.
    """

    def __init__(self, backend: CacheBackend) -> None:
        self._backend = backend

    def get_or_run(
        self,
        inputs: dict[str, Any],
        fn: Callable[[], dict[str, Any]],
    ) -> tuple[dict[str, Any], bool]:
        key = _cache_key(inputs)
        cached = self._backend.get(key)
        if cached is not None:
            return cached, True
        result = fn()
        self._backend.set(key, result)
        return result, False

    def key_for(self, inputs: dict[str, Any]) -> str:
        return _cache_key(inputs)
