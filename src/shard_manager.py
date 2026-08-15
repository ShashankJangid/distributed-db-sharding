"""
ShardManager — lifecycle management for a pool of database shards.
Each shard is a logical partition of a larger dataset.
"""
from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .consistent_hash import ConsistentHashRing

logger = logging.getLogger(__name__)


@dataclass
class ShardConfig:
    name: str
    host: str
    port: int = 5432
    db_name: str = "main"
    max_connections: int = 100
    replica: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.host}:{self.port}/{self.db_name}"


class ShardManager:
    """
    Manages a pool of shards backed by a ConsistentHashRing.

    Example::

        mgr = ShardManager(vnodes=150)
        mgr.register(ShardConfig("shard-0", "db0.internal"))
        mgr.register(ShardConfig("shard-1", "db1.internal"))
        mgr.register(ShardConfig("shard-2", "db2.internal"))

        cfg = mgr.locate("user:99182")
        print(cfg.dsn)
    """

    def __init__(self, vnodes: int = 150) -> None:
        self._ring = ConsistentHashRing(vnodes=vnodes)
        self._configs: Dict[str, ShardConfig] = {}

    def register(self, config: ShardConfig) -> None:
        """Add a shard to the pool."""
        self._configs[config.name] = config
        self._ring.add_shard(config.name)
        logger.info("Registered shard '%s' → %s", config.name, config.dsn)

    def deregister(self, shard_name: str) -> None:
        """Remove a shard (triggers key migration on next routing)."""
        self._ring.remove_shard(shard_name)
        self._configs.pop(shard_name, None)
        logger.warning("Deregistered shard '%s'. Keys will reroute.", shard_name)

    def locate(self, key: str) -> ShardConfig:
        """Return the shard config responsible for a given key."""
        shard_name = self._ring.get_shard(key)
        return self._configs[shard_name]

    def locate_replicas(self, key: str, n: int = 2) -> List[ShardConfig]:
        """Return n shard configs for replicated writes."""
        names = self._ring.get_shards(key, n)
        return [self._configs[name] for name in names]

    def all_shards(self) -> List[ShardConfig]:
        return list(self._configs.values())

    def shard_count(self) -> int:
        return len(self._configs)

    def distribution(self, sample_keys: List[str]) -> Dict[str, int]:
        """Show how sample keys distribute across shards (for analysis)."""
        counts: Dict[str, int] = {s: 0 for s in self._configs}
        for key in sample_keys:
            shard = self._ring.get_shard(key)
            counts[shard] += 1
        return counts
