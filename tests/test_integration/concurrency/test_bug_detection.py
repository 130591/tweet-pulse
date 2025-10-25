
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from tweetpulse.ingestion.deduplication import BloomDeduplicator


class TestDeduplicationBugDetection:
    """Tests that would catch the original Bloom Filter bug."""

    @pytest.mark.asyncio
    async def test_bloom_filter_wrong_key_bug(self):
        """This test catches the bug: using bloom_key instead of 'dedup:seen'."""

        # Create a mock Redis that tracks what keys are accessed
        redis_mock = AsyncMock()

        # Mock the Bloom filter operations
        redis_mock.bf.return_value.exists = AsyncMock(return_value=True)  # In bloom
        redis_mock.bf.return_value.add = AsyncMock()
        redis_mock.sadd = AsyncMock()

        # THE BUG: if implementation uses bloom_key instead of "dedup:seen"
        # This test will fail because sismember will be called with wrong key

        deduplicator = BloomDeduplicator(redis_mock, "test:bloom")

        # This should trigger the bug if it exists
        await deduplicator.is_duplicate("test_123")

        # Verify that sismember was called with the correct key
        # If there's a bug, it might call sismember("test:bloom", "test_123")
        # instead of sismember("dedup:seen", "test_123")

        redis_mock.sismember.assert_called_once_with("dedup:seen", "test_123")

    @pytest.mark.asyncio
    async def test_bloom_filter_false_positive_correct_key_usage(self):
        """Test that false positive handling uses correct keys."""

        redis_mock = AsyncMock()
        redis_mock.bf.return_value.exists = AsyncMock(return_value=True)  # False positive
        redis_mock.bf.return_value.add = AsyncMock()
        redis_mock.sismember = AsyncMock(return_value=False)  # Not in confirmation set
        redis_mock.sadd = AsyncMock()

        deduplicator = BloomDeduplicator(redis_mock, "test:bloom")

        await deduplicator.is_duplicate("test_false_positive")

        # Should check confirmation set with correct key
        redis_mock.sismember.assert_called_once_with("dedup:seen", "test_false_positive")

        # Should add to confirmation set with correct key
        redis_mock.sadd.assert_called_once_with("dedup:seen", "test_false_positive")


class TestBatchWriterDistributedLocking:
    """Tests for distributed locking in BatchWriter."""

    def test_batch_writer_requires_redis_for_locking(self):
        """Test that BatchWriter requires Redis for distributed locking."""
        from tweetpulse.ingestion.batch_writer import BatchWriter
        from unittest.mock import MagicMock

        # Should raise error if no Redis provided for locking
        with pytest.raises(AttributeError):
            writer = BatchWriter(
                session_factory=MagicMock(),
                staging_dir=Path("/tmp/test"),
                batch_size=10
            )
            # This would fail when trying to use distributed lock
            # because redis is None

    @pytest.mark.asyncio
    async def test_distributed_lock_acquisition_failure(self):
        """Test behavior when distributed lock cannot be acquired."""

        redis_mock = AsyncMock()
        redis_mock.set = AsyncMock(return_value=False)  # Lock acquisition fails

        from tweetpulse.ingestion.batch_writer import BatchWriter
        from tweetpulse.distributed.locking import RedisLock

        with patch('tweetpulse.ingestion.batch_writer.RedisLock') as mock_lock_class:
            mock_lock = AsyncMock()
            mock_lock.acquire = AsyncMock(return_value=False)
            mock_lock_class.return_value = mock_lock

            writer = BatchWriter(
                session_factory=MagicMock(),
                staging_dir=Path("/tmp/test"),
                redis_client=redis_mock
            )

            # Add tweets to trigger flush
            await writer.add_tweet({"id": "1", "text": "test"})
            await writer.add_tweet({"id": "2", "text": "test"})
            await writer.add_tweet({"id": "3", "text": "test"})

            # Flush should handle lock failure gracefully
            success = await writer.flush()

            # Should return False when lock cannot be acquired
            assert success is False

    @pytest.mark.asyncio
    async def test_multiple_batch_writers_coordination(self):
        """Test that multiple BatchWriter instances coordinate properly."""

        redis_mock = AsyncMock()

        # Mock successful lock acquisition for first writer
        redis_mock.set = AsyncMock(side_effect=[True, False])  # First succeeds, second fails

        from tweetpulse.ingestion.batch_writer import BatchWriter

        with patch('tweetpulse.ingestion.batch_writer.RedisLock') as mock_lock_class:
            mock_lock1 = AsyncMock()
            mock_lock1.acquire = AsyncMock(return_value=True)
            mock_lock1.release = AsyncMock()
            mock_lock1.extend = AsyncMock(return_value=True)

            mock_lock2 = AsyncMock()
            mock_lock2.acquire = AsyncMock(return_value=False)
            mock_lock2.release = AsyncMock()

            # Return different mocks for different instances
            mock_lock_class.side_effect = [mock_lock1, mock_lock2]

            # Create two writers
            writer1 = BatchWriter(
                session_factory=MagicMock(),
                staging_dir=Path("/tmp/test1"),
                redis_client=redis_mock
            )

            writer2 = BatchWriter(
                session_factory=MagicMock(),
                staging_dir=Path("/tmp/test2"),
                redis_client=redis_mock
            )

            # Both try to flush simultaneously
            success1 = await writer1.flush()
            success2 = await writer2.flush()

            # Only first should succeed
            assert success1 is True
            assert success2 is False

            # First should release lock
            mock_lock1.release.assert_called_once()


class TestPipelineDependencyInjection:
    """Tests for dependency injection in pipeline components."""

    def test_all_components_use_dependency_injection(self):
        """Test that all components can be injected with dependencies."""

        from tweetpulse.ingestion.pipeline import IngestionPipeline
        from tweetpulse.ingestion.batch_writer import BatchWriter
        from tweetpulse.ingestion.deduplication import BloomDeduplicator
        from unittest.mock import MagicMock

        # Test pipeline accepts all dependencies
        mock_redis = MagicMock()
        mock_db_url = "sqlite://test.db"

        pipeline = IngestionPipeline(
            keywords=["test"],
            staging_dir=Path("/tmp/test"),
            redis_client=mock_redis,
            database_url=mock_db_url
        )

        assert pipeline.redis is mock_redis
        assert pipeline.database_url == mock_db_url

        # Test BatchWriter accepts Redis
        writer = BatchWriter(
            session_factory=MagicMock(),
            staging_dir=Path("/tmp/test"),
            redis_client=mock_redis
        )

        assert writer.redis is mock_redis

        # Test deduplicator accepts Redis
        deduplicator = BloomDeduplicator(mock_redis, "test")
        assert deduplicator.redis is mock_redis


class TestMultiInstanceSimulation:
    """Simulate multiple instances to test distributed behavior."""

    @pytest.mark.asyncio
    async def test_concurrent_batch_writes_no_duplication(self):
        """Test that concurrent batch writes don't cause duplication."""

        redis_mock = AsyncMock()
        redis_mock.incrby = AsyncMock(return_value=3)
        redis_mock.scard = AsyncMock(return_value=3)

        from tweetpulse.ingestion.batch_writer import BatchWriter

        # Create multiple writers that will compete
        writers = []
        for i in range(3):
            writer = BatchWriter(
                session_factory=MagicMock(),
                staging_dir=Path(f"/tmp/test{i}"),
                batch_size=3,
                redis_client=redis_mock
            )
            writers.append(writer)

        # Simulate concurrent flush operations
        with patch('tweetpulse.ingestion.batch_writer.RedisLock') as mock_lock_class:
            # Only first writer gets the lock
            mock_lock = AsyncMock()
            mock_lock.acquire = AsyncMock(side_effect=[True, False, False])
            mock_lock.release = AsyncMock()
            mock_lock_class.return_value = mock_lock

            # All writers try to flush simultaneously
            results = await asyncio.gather(*[
                writer.flush() for writer in writers
            ])

            # Only one should succeed
            successful_flushes = sum(results)
            assert successful_flushes == 1

            # Lock should be acquired and released
            mock_lock.acquire.assert_called()
            mock_lock.release.assert_called_once()
