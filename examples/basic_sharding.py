"""
Demonstrate consistent hash sharding across 3 logical shards.
No real DB connection needed — shows routing decisions only.
"""
import sys; sys.path.insert(0, "..")

from src import ConsistentHashRing, ShardManager
from src.shard_manager import ShardConfig
from src.router import QueryRouter

# ── 1. Set up shards ─────────────────────────────────────────────────────────
manager = ShardManager(vnodes=150)
for i in range(3):
    manager.register(ShardConfig(
        name=f"shard-{i}",
        host=f"db{i}.internal",
        port=5432 + i,
        db_name="appdb",
    ))

print(f"Registered {manager.shard_count()} shards\n")

# ── 2. Route queries ──────────────────────────────────────────────────────────
router = QueryRouter(manager, shard_key="user_id")

user_ids = [101, 202, 303, 404, 505, 606, 707, 808, 909]
print("Routing decisions:")
for uid in user_ids:
    cfg = router.route({"user_id": uid})
    print(f"  user_id={uid:4d}  →  {cfg.name}  ({cfg.dsn})")

# ── 3. Distribution analysis ─────────────────────────────────────────────────
sample_keys = [f"user_id:{i}" for i in range(1, 10001)]
dist = manager.distribution(sample_keys)
print("\nKey distribution (10 000 keys):")
for shard, count in sorted(dist.items()):
    bar = "█" * (count // 100)
    print(f"  {shard}: {count:5d}  {bar}")
