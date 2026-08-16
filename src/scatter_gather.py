"""Scatter-Gather multi-shard executor for queries lacking a direct shard key."""
import concurrent.futures
from typing import Any, Callable, Dict, List
from .shard_manager import ShardManager

class ScatterGatherEngine:
    def __init__(self, manager: ShardManager, max_workers: int = 8):
        self.manager = manager
        self.max_workers = max_workers

    def execute_all(self, query_fn: Callable[[str], Any]) -> Dict[str, Any]:
        """Broadcasts a query to all shards concurrently and aggregates results."""
        shards = self.manager.all_shards()
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_shard = {
                executor.submit(query_fn, shard.name): shard.name
                for shard in shards
            }
            for future in concurrent.futures.as_completed(future_to_shard):
                shard_name = future_to_shard[future]
                try:
                    results[shard_name] = future.result()
                except Exception as exc:
                    results[shard_name] = {"error": str(exc)}
        return results
