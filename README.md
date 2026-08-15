# distributed-db-sharding

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

Horizontal database sharding engine using consistent hashing with virtual nodes (vnodes). Routes queries to the correct shard, supports replication factor N, and handles shard addition/removal with minimal key remapping.

## Architecture

```
Write(user_id=12345)
        │
        ▼
   QueryRouter
   (extracts shard key)
        │
        ▼
ConsistentHashRing
   (150 vnodes/shard)
        │
        ├──→ shard-0  (db0.internal:5432)
        ├──→ shard-1  (db1.internal:5433)
        └──→ shard-2  (db2.internal:5434)
```

## Key Concepts

**Consistent Hashing** — Keys map to positions on a hash ring (0–2³²). Each shard occupies `vnodes` positions. A key routes to the nearest shard clockwise. Adding a shard only remaps ~1/N keys.

**Virtual Nodes** — Each physical shard has `vnodes` (default 150) points on the ring. More vnodes = more even distribution at the cost of memory.

**Replication** — `locate_replicas(key, n=2)` walks the ring clockwise to find N distinct shards. Enables synchronous multi-shard writes for durability.

## Quick Start

```bash
git clone https://github.com/ShashankJangid/distributed-db-sharding.git
cd distributed-db-sharding
pip install -r requirements.txt

# Provision 3 Postgres shards via Docker
./scripts/setup_shards.sh 3

# Run the routing demo
python examples/basic_sharding.py
```

## Usage

```python
from src import ShardManager
from src.shard_manager import ShardConfig
from src.router import QueryRouter

manager = ShardManager(vnodes=150)
manager.register(ShardConfig("shard-0", "db0.internal"))
manager.register(ShardConfig("shard-1", "db1.internal"))
manager.register(ShardConfig("shard-2", "db2.internal"))

router = QueryRouter(manager, shard_key="user_id")
config = router.route({"user_id": 12345})
print(config.dsn)  # postgresql://db1.internal:5432/main
```

## Project Structure

```
distributed-db-sharding/
├── src/
│   ├── consistent_hash.py   # Hash ring with vnode support
│   ├── shard_manager.py     # Shard lifecycle + config
│   └── router.py            # Query routing by shard key
├── scripts/
│   ├── setup_shards.sh      # Docker-based shard provisioning
│   └── health_check.sh      # pg_isready health checks
├── examples/
│   └── basic_sharding.py    # Routing demo + distribution analysis
└── requirements.txt
```

## License

MIT
