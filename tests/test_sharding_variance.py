import sys; sys.path.insert(0, "..")
from src.consistent_hash import ConsistentHashRing

def test_hash_distribution_variance():
    ring = ConsistentHashRing(vnodes=100)
    ring.add_shard("s0")
    ring.add_shard("s1")
    ring.add_shard("s2")

    counts = {"s0": 0, "s1": 0, "s2": 0}
    for i in range(3000):
        s = ring.get_shard(f"key:{i}")
        counts[s] += 1

    # Ensure no single shard receives less than 20% or more than 45% of total keys
    for shard, count in counts.items():
        percentage = (count / 3000) * 100
        assert 20.0 <= percentage <= 45.0
