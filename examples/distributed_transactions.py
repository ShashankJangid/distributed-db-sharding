"""Simulation of 2-Phase Commit (2PC) protocol across multiple database shards."""
import sys; sys.path.insert(0, "..")
from src.shard_manager import ShardManager, ShardConfig

def simulate_2pc():
    mgr = ShardManager()
    mgr.register(ShardConfig("shard-0", "db0.internal"))
    mgr.register(ShardConfig("shard-1", "db1.internal"))

    print("Phase 1: PREPARE across shards...")
    votes = {"shard-0": True, "shard-1": True}
    all_ready = all(votes.values())
    print("All shards ready:", all_ready)

    print("Phase 2: COMMIT...")
    if all_ready:
        print("✓ Transaction COMMITTED globally across all partitions.")
    else:
        print("✗ ABORT rolled back on all participants.")

if __name__ == "__main__":
    simulate_2pc()
