"""
QueryRouter — routes SQL queries to the correct shard based on a shard key.
Parses a simple shard_key → value pattern from query params.
"""
from __future__ import annotations
import logging
import re
from typing import Any, Dict, Optional, Tuple

from .shard_manager import ShardConfig, ShardManager

logger = logging.getLogger(__name__)


class QueryRouter:
    """
    Lightweight query router — extracts the shard key from a query
    dict and returns the correct ShardConfig.

    Example::

        router = QueryRouter(manager, shard_key="user_id")
        config = router.route({"user_id": 12345, "action": "purchase"})
        # connects to the shard owning user_id=12345
    """

    def __init__(self, manager: ShardManager, shard_key: str = "id") -> None:
        self.manager = manager
        self.shard_key = shard_key

    def route(self, params: Dict[str, Any]) -> ShardConfig:
        """Route a parameter dict to its responsible shard."""
        value = params.get(self.shard_key)
        if value is None:
            raise KeyError(
                f"Shard key '{self.shard_key}' not found in params: {list(params.keys())}"
            )
        key = f"{self.shard_key}:{value}"
        config = self.manager.locate(key)
        logger.debug("Routing key='%s' → shard='%s'", key, config.name)
        return config

    def route_replicated(
        self, params: Dict[str, Any], replicas: int = 2
    ) -> list[ShardConfig]:
        """Route with replication factor — returns N shard configs."""
        value = params.get(self.shard_key)
        if value is None:
            raise KeyError(f"Shard key '{self.shard_key}' not found in params.")
        key = f"{self.shard_key}:{value}"
        return self.manager.locate_replicas(key, n=replicas)
