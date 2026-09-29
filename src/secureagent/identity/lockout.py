"""Lockout policy: free attempts, then exponential backoff to a ceiling (§5.2).

Keys are namespaced `acct:` and `client:`. Both are checked on every attempt.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import time

from secureagent.store.lockout_store import LockoutStore


@dataclass(frozen=True)
class LockoutPolicy:
    free_attempts: int = 3
    base_delay_seconds: float = 30.0
    max_delay_seconds: float = 900.0

    def delay_after(self, failures: int) -> float:
        """Seconds to wait after this many consecutive failures."""
        if failures < self.free_attempts:
            return 0.0
        return float(
            min(
                self.base_delay_seconds * 2 ** (failures - self.free_attempts),
                self.max_delay_seconds,
            )
        )


class Lockout:
    def __init__(
        self,
        store: LockoutStore,
        policy: LockoutPolicy | None = None,
        *,
        clock: Callable[[], float] = time,
    ) -> None:
        self._store = store
        self._policy = policy or LockoutPolicy()
        self._clock = clock

    def retry_after(self, *keys: str) -> float:
        """The longest remaining wait across the given keys; 0.0 if none applies."""
        now = self._clock()
        waits = [max(0.0, self._store.get(key)[1] - now) for key in keys]
        return max(waits, default=0.0)

    def record_failure(self, *keys: str) -> None:
        now = self._clock()
        for key in keys:
            failures = self._store.get(key)[0] + 1
            self._store.set(key, failures, now + self._policy.delay_after(failures))

    def record_success(self, key: str) -> None:
        self._store.clear(key)
