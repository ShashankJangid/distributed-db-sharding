"""Connection pooling manager with health checks and circuit breaker logic."""
import time
import logging
from typing import Dict
from .shard_manager import ShardConfig

logger = logging.getLogger(__name__)

class ShardConnectionPool:
    def __init__(self, failure_threshold: int = 3, cooldown_sec: float = 30.0):
        self.failure_threshold = failure_threshold
        self.cooldown_sec = cooldown_sec
        self._failures: Dict[str, int] = {}
        self._tripped_until: Dict[str, float] = {}

    def record_failure(self, shard_name: str):
        self._failures[shard_name] = self._failures.get(shard_name, 0) + 1
        if self._failures[shard_name] >= self.failure_threshold:
            self._tripped_until[shard_name] = time.time() + self.cooldown_sec
            logger.error("🚨 Circuit breaker TRIPPED for shard '%s' for %.0fs", shard_name, self.cooldown_sec)

    def record_success(self, shard_name: str):
        self._failures[shard_name] = 0
        self._tripped_until.pop(shard_name, None)

    def is_available(self, shard_name: str) -> bool:
        if shard_name in self._tripped_until:
            if time.time() < self._tripped_until[shard_name]:
                return False
            self.record_success(shard_name)
        return True
