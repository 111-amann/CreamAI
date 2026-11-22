"""
app/cache.py - Lightweight In-Memory Bounded Cache for PyDocsPal.

Features:
- Bounded maximum entries with LRU/FIFO eviction
- Time-to-Live (TTL) expiration per entry
- Thread-safe operations using threading.Lock
- Hit/Miss telemetry tracking
- Deterministic key generation
- Reset and bypass support for deterministic testing
"""

import hashlib
import json
import os
import threading
import time
from typing import Any, Optional


class SimpleCache:
    """
    Thread-safe, lightweight, bounded in-memory cache with TTL expiration
    and hit/miss telemetry tracking.
    """

    def __init__(
        self,
        max_entries: int = 1000,
        default_ttl: int = 300,
    ):
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self._cache: dict[str, tuple[Any, float]] = {}  # key -> (value, expire_at)
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def generate_key(self, prefix: str, **kwargs: Any) -> str:
        """Create a deterministic cache key from prefix and sorted keyword arguments."""
        serialized = json.dumps(kwargs, sort_keys=True, default=str)
        hashed = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
        return f"{prefix}:{hashed}"

    def get(self, key: str) -> Optional[Any]:
        """Retrieve an entry from cache if present and not expired."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, expire_at = self._cache[key]
            if time.time() > expire_at:
                # Expired entry
                del self._cache[key]
                self._misses += 1
                return None

            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store an entry in the cache with a specified or default TTL."""
        ttl_seconds = ttl if ttl is not None else self.default_ttl
        expire_at = time.time() + ttl_seconds

        with self._lock:
            # If at max capacity, evict expired items first
            if len(self._cache) >= self.max_entries and key not in self._cache:
                now = time.time()
                expired_keys = [k for k, (_, exp) in self._cache.items() if now > exp]
                for k in expired_keys:
                    del self._cache[k]

                # If still at capacity, evict oldest entry
                if len(self._cache) >= self.max_entries:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]

            self._cache[key] = (value, expire_at)

    def delete(self, key: str) -> bool:
        """Delete a single key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all entries and reset stats for deterministic testing."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict[str, Any]:
        """Return cache telemetry including hits, misses, size, and hit rate."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests) if total_requests > 0 else 0.0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._cache),
                "max_entries": self.max_entries,
                "hit_rate": round(hit_rate, 4),
                "ttl_seconds": self.default_ttl,
            }

    def __contains__(self, key: str) -> bool:
        with self._lock:
            if key not in self._cache:
                return False
            _, expire_at = self._cache[key]
            if time.time() > expire_at:
                del self._cache[key]
                return False
            return True


# Default global instance configured via environment variables
DEFAULT_MAX_ENTRIES = int(os.getenv("CACHE_MAX_ENTRIES", "1000"))
DEFAULT_CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "300"))

query_cache = SimpleCache(
    max_entries=DEFAULT_MAX_ENTRIES,
    default_ttl=DEFAULT_CACHE_TTL,
)
