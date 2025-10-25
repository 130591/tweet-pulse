"""
Distributed locking utilities for multi-instance safety.
"""
import asyncio
import logging
import time
import uuid
from typing import Optional
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisLock:
    """
    Distributed lock using Redis for multi-instance coordination.

    Based on Redis SET NX PX pattern with proper cleanup.
    """

    def __init__(self, redis_client: Redis, lock_key: str, timeout_seconds: int = 30):
      self.redis = redis_client
      self.lock_key = lock_key
      self.timeout_seconds = timeout_seconds
      self._lock_value: Optional[str] = None

    async def __aenter__(self) -> 'RedisLock':
      """Acquire the distributed lock."""
      await self.acquire()
      return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
      """Release the distributed lock."""
      await self.release()

    async def acquire(self) -> bool:
      """
      Try to acquire the distributed lock.

      Returns:
          bool: True if lock acquired, False otherwise
      """
      self._lock_value = str(uuid.uuid4())

      # Try to set the lock with NX (only if doesn't exist) and PX (expire)
      success = await self.redis.set(
        self.lock_key,
        self._lock_value,
        ex=self.timeout_seconds,
        nx=True  # Only set if key doesn't exist
      )

      if success:
        logger.debug(f"Distributed lock acquired: {self.lock_key}")
        return True
      else:
        logger.debug(f"Failed to acquire distributed lock: {self.lock_key}")
        return False

    async def release(self) -> bool:
        """
        Release the distributed lock.

        Returns:
            bool: True if lock was released, False otherwise
        """
        if not self._lock_value:
          return False

        try:
          # Use Lua script to ensure atomicity
          lua_script = """
          if redis.call('GET', KEYS[1]) == ARGV[1] then
              redis.call('DEL', KEYS[1])
              return 1
          else
              return 0
          end
          """

          result = await self.redis.eval(
            lua_script,
            keys=[self.lock_key],
            args=[self._lock_value]
          )

          if result:
            logger.debug(f"Distributed lock released: {self.lock_key}")
            return True
          else:
            logger.warning(f"Failed to release distributed lock: {self.lock_key}")
            return False

        finally:
            self._lock_value = None

    async def extend(self, additional_seconds: int = None) -> bool:
        """
        Extend the lock timeout.

        Args:
            additional_seconds: Additional seconds to add (defaults to original timeout)

        Returns:
            bool: True if extended successfully
        """
        if not self._lock_value:
          return False

        if additional_seconds is None:
          additional_seconds = self.timeout_seconds

        # Use Lua script for atomic extend
        lua_script = """
        if redis.call('GET', KEYS[1]) == ARGV[1] then
          redis.call('PEXPIRE', KEYS[1], ARGV[2])
          return 1
        else
            return 0
        end
        """

        result = await self.redis.eval(
          lua_script,
          keys=[self.lock_key],
          args=[self._lock_value, additional_seconds * 1000]  # PEXPIRE uses milliseconds
        )

        if result:
          logger.debug(f"Distributed lock extended: {self.lock_key} (+{additional_seconds}s)")
          return True
        else:
          logger.warning(f"Failed to extend distributed lock: {self.lock_key}")
          return False


class DistributedLockManager:
    """
    Manager for distributed locks with automatic cleanup and monitoring.
    """

    def __init__(self, redis_client: Redis):
      self.redis = redis_client
      self._active_locks: dict = {}

    async def acquire_lock(self, lock_name: str, timeout_seconds: int = 30) -> Optional[RedisLock]:
        """
        Acquire a named lock.

        Args:
            lock_name: Name of the lock
            timeout_seconds: Lock timeout in seconds

        Returns:
            RedisLock if acquired, None otherwise
        """
        lock_key = f"distributed_lock:{lock_name}"
        lock = RedisLock(self.redis, lock_key, timeout_seconds)

        if await lock.acquire():
          self._active_locks[lock_name] = lock
          return lock
        else:
          return None

    async def cleanup_stale_locks(self):
        """Clean up any stale locks (for maintenance)."""
        pattern = "distributed_lock:*"
        keys = await self.redis.keys(pattern)

        for key in keys:
          # Check if lock has expired
          ttl = await self.redis.pttl(key)
          if ttl == -2:  # Key doesn't exist
            continue
          elif ttl == -1:  # No expiration
            logger.warning(f"Found lock without expiration: {key}")
            await self.redis.delete(key)

    def get_active_locks(self) -> list:
      """Get list of currently held locks."""
      return list(self._active_locks.keys())
