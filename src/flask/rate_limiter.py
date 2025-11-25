from __future__ import annotations

from collections import defaultdict
from collections import deque
from threading import Lock
from time import monotonic

__all__ = ("MemoryRateLimiter",)


class MemoryRateLimiter:
    """Simple in-memory, per-key fixed window rate limiter.

    The limiter stores request timestamps in monotonic time buckets. It is
    designed for small Flask applications and the built-in development server,
    not as a production-grade distributed limiter.
    """

    def __init__(self, limit: int, window: float) -> None:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if window <= 0:
            raise ValueError("window must be greater than 0 seconds")

        self.limit = limit
        self.window = window
        self._requests: defaultdict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def hit(self, key: str) -> tuple[bool, float | None]:
        """Record a hit for *key*.

        Returns a tuple ``(allowed, retry_after)`` where *allowed* indicates if
        the request can proceed. When *allowed* is ``False`` the second value is
        the remaining seconds until a new request would be accepted.
        """

        now = monotonic()
        window_start = now - self.window

        with self._lock:
            bucket = self._requests[key]

            while bucket and bucket[0] <= window_start:
                bucket.popleft()

            if len(bucket) >= self.limit:
                retry_after = max(0.0, self.window - (now - bucket[0]))
                return False, retry_after

            bucket.append(now)

        return True, None
