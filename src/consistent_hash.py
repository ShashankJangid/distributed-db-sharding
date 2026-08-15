"""
Consistent hashing ring for distributing keys across shards.
Uses virtual nodes (vnodes) to balance load when shards are added/removed.
"""
from __future__ import annotations
import hashlib
import logging
from bisect import bisect, insort
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ConsistentHashRing:
    """
    A consistent hash ring with virtual node support.

    Virtual nodes (vnodes) improve distribution: each physical shard
    is represented by `vnodes` points on the ring. Default is 150.

    Example::

        ring = ConsistentHashRing(vnodes=150)
        ring.add_shard("shard-0")
        ring.add_shard("shard-1")
        ring.add_shard("shard-2")
        shard = ring.get_shard("user:12345")  # "shard-1"
    """

    def __init__(self, vnodes: int = 150) -> None:
        if vnodes < 1:
            raise ValueError("vnodes must be >= 1")
        self.vnodes = vnodes
        self._ring: Dict[int, str] = {}   # hash_point → shard_name
        self._sorted_keys: List[int] = []
        self._shards: List[str] = []

    # ------------------------------------------------------------------
    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def _vnode_key(self, shard: str, n: int) -> str:
        return f"{shard}::vn{n}"

    # ------------------------------------------------------------------
    def add_shard(self, shard: str) -> None:
        """Register a new shard and distribute its vnodes on the ring."""
        if shard in self._shards:
            logger.warning("Shard '%s' already exists — skipped.", shard)
            return
        self._shards.append(shard)
        for i in range(self.vnodes):
            point = self._hash(self._vnode_key(shard, i))
            self._ring[point] = shard
            insort(self._sorted_keys, point)
        logger.info("Added shard '%s' (%d vnodes).", shard, self.vnodes)

    def remove_shard(self, shard: str) -> None:
        """Remove a shard and all its vnodes from the ring."""
        if shard not in self._shards:
            raise KeyError(f"Shard '{shard}' not found.")
        self._shards.remove(shard)
        for i in range(self.vnodes):
            point = self._hash(self._vnode_key(shard, i))
            self._ring.pop(point, None)
            idx = bisect(self._sorted_keys, point) - 1
            if 0 <= idx < len(self._sorted_keys) and self._sorted_keys[idx] == point:
                self._sorted_keys.pop(idx)
        logger.info("Removed shard '%s'.", shard)

    def get_shard(self, key: str) -> str:
        """Return the shard responsible for the given key."""
        if not self._ring:
            raise RuntimeError("Ring is empty — add shards first.")
        h = self._hash(key)
        idx = bisect(self._sorted_keys, h) % len(self._sorted_keys)
        return self._ring[self._sorted_keys[idx]]

    def get_shards(self, key: str, n: int) -> List[str]:
        """Return n distinct shards for replication (walks the ring clockwise)."""
        if n > len(self._shards):
            raise ValueError(f"Requested {n} shards but only {len(self._shards)} exist.")
        seen: set = set()
        result: List[str] = []
        h = self._hash(key)
        start = bisect(self._sorted_keys, h) % len(self._sorted_keys)
        i = start
        while len(result) < n:
            shard = self._ring[self._sorted_keys[i]]
            if shard not in seen:
                seen.add(shard)
                result.append(shard)
            i = (i + 1) % len(self._sorted_keys)
        return result

    @property
    def shards(self) -> List[str]:
        return list(self._shards)

    def __repr__(self) -> str:
        return f"ConsistentHashRing(shards={self._shards}, vnodes={self.vnodes})"
