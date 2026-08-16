"""
Zero-downtime shard rebalancing and online key migration engine.
Computes minimal delta keys that must move when adding or removing shards.
"""
import logging
from typing import Dict, List, Tuple
from .consistent_hash import ConsistentHashRing

logger = logging.getLogger(__name__)

class ShardMigrator:
    def __init__(self, current_ring: ConsistentHashRing, new_ring: ConsistentHashRing):
        self.current_ring = current_ring
        self.new_ring = new_ring

    def plan_migration(self, sample_keys: List[str]) -> Dict[Tuple[str, str], List[str]]:
        """
        Computes the mapping of (source_shard -> target_shard) : [keys_to_move]
        Only keys whose hash location changes are scheduled for migration.
        """
        migration_plan: Dict[Tuple[str, str], List[str]] = {}
        for key in sample_keys:
            old_shard = self.current_ring.get_shard(key)
            new_shard = self.new_ring.get_shard(key)
            if old_shard != new_shard:
                pair = (old_shard, new_shard)
                migration_plan.setdefault(pair, []).append(key)
        logger.info("Migration plan computed for %d keys across %d shard pairs", len(sample_keys), len(migration_plan))
        return migration_plan
