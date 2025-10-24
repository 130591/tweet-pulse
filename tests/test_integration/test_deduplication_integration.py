"""
Integration tests for Deduplication component.
Testing deterministic behavior for duplicate detection.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tweetpulse.ingestion.deduplication import BloomDeduplicator


class TestDeduplicationIntegration:
    """Test Deduplication component with deterministic behavior."""
    
    @pytest.mark.asyncio
    async def test_first_tweet_not_duplicate(self, clean_redis):
        """Test first occurrence of tweet is not marked as duplicate."""
        # Mock the Bloom filter methods
        clean_redis.bf = MagicMock()
        clean_redis.bf.return_value.exists = AsyncMock(return_value=False)
        clean_redis.bf.return_value.add = AsyncMock()
        clean_redis.sismember = AsyncMock(return_value=False)
        clean_redis.sadd = AsyncMock()
        
        deduplicator = BloomDeduplicator(redis=clean_redis, key="dedup:bloom")
        
        is_dup = await deduplicator.is_duplicate("tweet_123")
        
        assert is_dup is False
        clean_redis.bf.return_value.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_second_occurrence_is_duplicate(self, clean_redis):
        """Test second occurrence of same tweet is marked as duplicate."""
        # Mock Bloom filter to simulate tweet already exists
        clean_redis.bf = MagicMock()
        bf_mock = clean_redis.bf.return_value
        
        # First call: exists returns True (in bloom)
        # Second call: sismember returns True (confirmed duplicate)
        bf_mock.exists = AsyncMock(return_value=True)
        bf_mock.add = AsyncMock()
        clean_redis.sismember = AsyncMock(return_value=True)
        
        deduplicator = BloomDeduplicator(redis=clean_redis, key="dedup:bloom")
        
        is_dup = await deduplicator.is_duplicate("tweet_123")
        
        assert is_dup is True
    
    @pytest.mark.asyncio
    async def test_different_tweets_not_duplicates(self, clean_redis):
        """Test different tweets are not marked as duplicates."""
        clean_redis.bf = MagicMock()
        bf_mock = clean_redis.bf.return_value
        bf_mock.exists = AsyncMock(return_value=False)
        bf_mock.add = AsyncMock()
        clean_redis.sismember = AsyncMock(return_value=False)
        clean_redis.sadd = AsyncMock()
        
        deduplicator = BloomDeduplicator(redis=clean_redis, key="dedup:bloom")
        
        # Check multiple different tweets
        tweet_ids = ["tweet_001", "tweet_002", "tweet_003"]
        
        for tweet_id in tweet_ids:
            is_dup = await deduplicator.is_duplicate(tweet_id)
            assert is_dup is False
    
    @pytest.mark.asyncio
    async def test_bloom_filter_false_positive_handling(self, clean_redis):
        """Test handling of Bloom filter false positive."""
        clean_redis.bf = MagicMock()
        bf_mock = clean_redis.bf.return_value
        
        # Bloom filter says it exists (false positive)
        bf_mock.exists = AsyncMock(return_value=True)
        bf_mock.add = AsyncMock()
        
        # But it's not in the confirmation set
        clean_redis.sismember = AsyncMock(return_value=False)
        clean_redis.sadd = AsyncMock()
        
        deduplicator = BloomDeduplicator(redis=clean_redis, key="dedup:bloom")
        
        is_dup = await deduplicator.is_duplicate("tweet_999")
        
        # Should not be marked as duplicate (false positive handled)
        assert is_dup is False
        
        # Should add to both bloom and confirmation set
        bf_mock.add.assert_called()
        clean_redis.sadd.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deduplication_order_independence(self, clean_redis):
        """Test deduplication works regardless of check order."""
        clean_redis.bf = MagicMock()
        bf_mock = clean_redis.bf.return_value
        
        # Track which tweets we've seen
        seen_tweets = set()
        
        async def exists_side_effect(key, tweet_id):
            return tweet_id in seen_tweets
        
        async def add_side_effect(key, tweet_id):
            seen_tweets.add(tweet_id)
        
        bf_mock.exists = AsyncMock(side_effect=exists_side_effect)
        bf_mock.add = AsyncMock(side_effect=add_side_effect)
        clean_redis.sismember = AsyncMock(side_effect=lambda k, tid: tid in seen_tweets)
        clean_redis.sadd = AsyncMock()
        
        deduplicator = BloomDeduplicator(redis=clean_redis, key="dedup:bloom")
        
        # Check tweets in different order
        order1 = ["A", "B", "C", "A", "B"]
        results1 = []
        
        for tweet_id in order1:
            is_dup = await deduplicator.is_duplicate(tweet_id)
            results1.append((tweet_id, is_dup))
        
        # Reset
        seen_tweets.clear()
        
        order2 = ["C", "A", "B", "A", "C"]
        results2 = []
        
        for tweet_id in order2:
            is_dup = await deduplicator.is_duplicate(tweet_id)
            results2.append((tweet_id, is_dup))
        
        # First occurrence should never be duplicate
        assert results1[0][1] is False  # A
        assert results1[1][1] is False  # B
        assert results1[2][1] is False  # C
        
        assert results2[0][1] is False  # C
        assert results2[1][1] is False  # A
        assert results2[2][1] is False  # B
        
        # Second occurrence should always be duplicate
        assert results1[3][1] is True   # A again
        assert results1[4][1] is True   # B again
        
        assert results2[3][1] is True   # A again
        assert results2[4][1] is True   # C again
    
    @pytest.mark.asyncio
    async def test_concurrent_deduplication_checks(self, clean_redis):
        """Test concurrent deduplication checks don't cause race conditions."""
        import asyncio
        
        clean_redis.bf = MagicMock()
        bf_mock = clean_redis.bf.return_value
        
        seen_tweets = set()
        lock = asyncio.Lock()
        
        async def exists_side_effect(key, tweet_id):
            async with lock:
                return tweet_id in seen_tweets
        
        async def add_side_effect(key, tweet_id):
            async with lock:
                seen_tweets.add(tweet_id)
        
        bf_mock.exists = AsyncMock(side_effect=exists_side_effect)
        bf_mock.add = AsyncMock(side_effect=add_side_effect)
        
        async def sismember_side_effect(k, tid):
            async with lock:
                return tid in seen_tweets
        
        clean_redis.sismember = AsyncMock(side_effect=sismember_side_effect)
        clean_redis.sadd = AsyncMock()
        
        deduplicator = BloomDeduplicator(redis=clean_redis, key="dedup:bloom")
        
        # Check same tweet concurrently
        results = await asyncio.gather(*[
            deduplicator.is_duplicate("tweet_concurrent")
            for _ in range(10)
        ])
        
        # At least one should be False (first check)
        # Others might be True (duplicates detected)
        assert False in results
        assert sum(not r for r in results) >= 1  # At least one non-duplicate
    
    @pytest.mark.asyncio
    async def test_deduplicator_with_numeric_ids(self, clean_redis):
        """Test deduplicator works with numeric tweet IDs."""
        clean_redis.bf = MagicMock()
        bf_mock = clean_redis.bf.return_value
        bf_mock.exists = AsyncMock(return_value=False)
        bf_mock.add = AsyncMock()
        clean_redis.sismember = AsyncMock(return_value=False)
        clean_redis.sadd = AsyncMock()
        
        deduplicator = BloomDeduplicator(redis=clean_redis, key="dedup:bloom")
        
        # Numeric IDs (converted to string)
        numeric_ids = ["1234567890", "9876543210", "1111111111"]
        
        for tweet_id in numeric_ids:
            is_dup = await deduplicator.is_duplicate(tweet_id)
            assert is_dup is False
    
    @pytest.mark.asyncio
    async def test_deduplicator_empty_id_handling(self, clean_redis):
        """Test deduplicator handles empty/invalid IDs gracefully."""
        clean_redis.bf = MagicMock()
        bf_mock = clean_redis.bf.return_value
        bf_mock.exists = AsyncMock(return_value=False)
        bf_mock.add = AsyncMock()
        clean_redis.sismember = AsyncMock(return_value=False)
        clean_redis.sadd = AsyncMock()
        
        deduplicator = BloomDeduplicator(redis=clean_redis, key="dedup:bloom")
        
        # Empty string ID
        is_dup = await deduplicator.is_duplicate("")
        
        # Should handle gracefully (not crash)
        assert isinstance(is_dup, bool)
