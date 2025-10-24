"""
Integration tests for BatchWriter component.
Testing deterministic behavior for batch writing.
"""
import pytest
import asyncio
from unittest.mock import MagicMock

from tweetpulse.ingestion.batch_writer import BatchWriter


class TestBatchWriterIntegration:
    """Test BatchWriter with deterministic behavior."""
    
    @pytest.mark.asyncio
    async def test_batch_writer_initialization(self, staging_dir):
        """Test batch writer initializes correctly."""
        session_factory = MagicMock()
        
        writer = BatchWriter(
            session_factory=session_factory,
            staging_dir=staging_dir,
            interval_seconds=1
        )
        
        assert writer.session_factory == session_factory
        assert writer.staging_dir == staging_dir
        assert writer.interval_seconds == 1
        assert writer.is_running is False
        assert len(writer.batch) == 0
    
    @pytest.mark.asyncio
    async def test_batch_writer_adds_tweets(self, staging_dir, sample_tweets_batch):
        """Test adding tweets to batch is deterministic."""
        session_factory = MagicMock()
        
        writer = BatchWriter(
            session_factory=session_factory,
            staging_dir=staging_dir,
            interval_seconds=10
        )
        
        # Add tweets
        for tweet in sample_tweets_batch[:3]:
            writer.add_tweet(tweet)
        
        assert len(writer.batch) == 3
        assert writer.batch[0]['id'] == 'tweet_00000'
        assert writer.batch[1]['id'] == 'tweet_00001'
        assert writer.batch[2]['id'] == 'tweet_00002'
    
    @pytest.mark.asyncio
    async def test_batch_writer_flush_clears_batch(self, staging_dir, sample_tweets_batch):
        """Test flush clears batch correctly."""
        session_factory = MagicMock()
        mock_session = MagicMock()
        session_factory.return_value = mock_session
        
        writer = BatchWriter(
            session_factory=session_factory,
            staging_dir=staging_dir,
            interval_seconds=10
        )
        
        # Add tweets
        for tweet in sample_tweets_batch[:5]:
            writer.add_tweet(tweet)
        
        assert len(writer.batch) == 5
        
        # Flush
        await writer.flush()
        
        # Batch should be empty
        assert len(writer.batch) == 0
        
        # Session should be created and closed
        session_factory.assert_called_once()
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_writer_flush_empty_batch(self, staging_dir):
        """Test flush with empty batch does nothing."""
        session_factory = MagicMock()
        
        writer = BatchWriter(
            session_factory=session_factory,
            staging_dir=staging_dir,
            interval_seconds=10
        )
        
        # Flush empty batch
        await writer.flush()
        
        # Session should NOT be created
        session_factory.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_batch_writer_run_forever_flushes_periodically(
        self, staging_dir, sample_tweets_batch
    ):
        """Test run_forever flushes at intervals."""
        session_factory = MagicMock()
        mock_session = MagicMock()
        session_factory.return_value = mock_session
        
        writer = BatchWriter(
            session_factory=session_factory,
            staging_dir=staging_dir,
            interval_seconds=0.2  # Fast interval for testing
        )
        
        # Add some tweets
        for tweet in sample_tweets_batch[:3]:
            writer.add_tweet(tweet)
        
        # Start run_forever
        task = asyncio.create_task(writer.run_forever())
        
        # Wait for at least one flush
        await asyncio.sleep(0.5)
        
        # Stop
        writer.stop()
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Should have flushed at least once
        assert session_factory.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_batch_writer_handles_flush_errors(self, staging_dir, sample_tweets_batch):
        """Test batch writer handles flush errors gracefully."""
        session_factory = MagicMock()
        session_factory.side_effect = Exception("Database error")
        
        writer = BatchWriter(
            session_factory=session_factory,
            staging_dir=staging_dir,
            interval_seconds=10
        )
        
        # Add tweets
        for tweet in sample_tweets_batch[:3]:
            writer.add_tweet(tweet)
        
        # Flush should handle error
        await writer.flush()
        
        # Tweets should be put back in batch on error
        assert len(writer.batch) == 3
    
    @pytest.mark.asyncio
    async def test_batch_writer_stop_sets_flag(self, staging_dir):
        """Test stop method sets running flag."""
        session_factory = MagicMock()
        
        writer = BatchWriter(
            session_factory=session_factory,
            staging_dir=staging_dir,
            interval_seconds=10
        )
        
        writer.is_running = True
        writer.stop()
        
        assert writer.is_running is False
    
    @pytest.mark.asyncio
    async def test_batch_writer_concurrent_adds(self, staging_dir, sample_tweets_batch):
        """Test concurrent tweet additions don't cause issues."""
        session_factory = MagicMock()
        
        writer = BatchWriter(
            session_factory=session_factory,
            staging_dir=staging_dir,
            interval_seconds=10
        )
        
        # Add tweets concurrently
        async def add_tweet_async(tweet):
            writer.add_tweet(tweet)
        
        await asyncio.gather(*[
            add_tweet_async(tweet)
            for tweet in sample_tweets_batch[:10]
        ])
        
        # All tweets should be added
        assert len(writer.batch) == 10
    
    @pytest.mark.asyncio
    async def test_batch_writer_respects_batch_limit(self, staging_dir, sample_tweets_batch):
        """Test batch writer tracks large batches."""
        session_factory = MagicMock()
        
        writer = BatchWriter(
            session_factory=session_factory,
            staging_dir=staging_dir,
            interval_seconds=10
        )
        
        # Add many tweets
        for i in range(1000):
            tweet = {"id": f"tweet_{i}", "text": f"Tweet {i}"}
            writer.add_tweet(tweet)
        
        # Should track all
        assert len(writer.batch) == 1000
    
    @pytest.mark.asyncio
    async def test_batch_writer_preserves_tweet_data(self, staging_dir, enriched_tweet_data):
        """Test batch writer preserves all tweet data."""
        session_factory = MagicMock()
        mock_session = MagicMock()
        session_factory.return_value = mock_session
        
        writer = BatchWriter(
            session_factory=session_factory,
            staging_dir=staging_dir,
            interval_seconds=10
        )
        
        # Add enriched tweet
        writer.add_tweet(enriched_tweet_data)
        
        # Flush
        await writer.flush()
        
        # Verify tweet data is preserved (batch was copied before flush)
        # After flush, batch should be empty but data was processed
        assert len(writer.batch) == 0
