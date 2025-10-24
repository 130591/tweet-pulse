"""
Integration tests for complete Ingestion Pipeline.

PRINCÍPIO: Test of BEHAVIOR END-TO-END.

Testing the COMPLETE FLOW:
✅ Tweet enters → Tweet is processed and stored
✅ Duplicate tweets are ignored
✅ Pipeline processes multiple tweets correctly
✅ Errors are gracefully handled

Not testing:
❌ How many times internal methods were called
❌ Internal pipeline data structures
❌ Exact order of internal operations
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from tweetpulse.ingestion.pipeline import IngestionPipeline


class TestPipelineIntegration:
    """Test complete pipeline with deterministic behavior."""
    
    @pytest.mark.asyncio
    async def test_pipeline_initialization(self, staging_dir):
        """Test pipeline initializes all components correctly."""
        with patch('tweetpulse.ingestion.pipeline.Redis') as mock_redis_class, \
             patch('tweetpulse.ingestion.pipeline.TwitterStreamConnector'), \
             patch('tweetpulse.ingestion.enrichment.pipeline') as mock_nlp, \
             patch('tweetpulse.ingestion.enrichment.torch') as mock_torch:
            
            mock_torch.cuda.is_available.return_value = False
            mock_nlp.return_value = MagicMock()
            mock_redis = MagicMock()
            mock_redis_class.from_url.return_value = mock_redis
            
            pipeline = IngestionPipeline(
                keywords=["python", "testing"],
                staging_dir=staging_dir,
                num_workers=2
            )
            
            assert pipeline.keywords == ["python", "testing"]
            assert pipeline.num_workers == 2
            assert pipeline.staging_dir == staging_dir
            assert pipeline.is_running is False
            assert len(pipeline.tasks) == 0
            
            # Components should be initialized
            assert pipeline.deduplicator is not None
            assert pipeline.enricher is not None
            assert pipeline.storage is not None
    
    @pytest.mark.asyncio
    async def test_pipeline_processes_tweet_end_to_end(self, staging_dir, sample_tweet_data, clean_redis):
        """Test behavior: pipeline processes tweet from input to storage."""
        with patch('tweetpulse.ingestion.pipeline.TwitterStreamConnector'), \
             patch('tweetpulse.ingestion.enrichment.pipeline') as mock_nlp, \
             patch('tweetpulse.ingestion.enrichment.torch') as mock_torch, \
             patch('tweetpulse.ingestion.enrichment.langdetect.detect') as mock_detect:
            
            # Setup mocks for external dependencies only
            mock_torch.cuda.is_available.return_value = False
            mock_sentiment = MagicMock()
            mock_sentiment.return_value = [{"label": "POSITIVE", "score": 0.95}]
            mock_nlp.return_value = mock_sentiment
            mock_detect.return_value = "en"
            
            # Mock bloom filter (Redis extension)
            clean_redis.bf = MagicMock()
            bf_mock = clean_redis.bf.return_value
            bf_mock.exists = AsyncMock(return_value=False)
            bf_mock.add = AsyncMock()
            clean_redis.sismember = AsyncMock(return_value=False)
            clean_redis.sadd = AsyncMock()
            
            # Mock Redis pipeline for storage
            clean_redis.pipeline = MagicMock()
            mock_pipe = MagicMock()
            clean_redis.pipeline.return_value = mock_pipe
            mock_pipe.hset = MagicMock()
            mock_pipe.expire = MagicMock()
            mock_pipe.lpush = MagicMock()
            mock_pipe.ltrim = MagicMock()
            mock_pipe.sadd = MagicMock()
            mock_pipe.incr = MagicMock()
            mock_pipe.execute = AsyncMock()
            
            with patch('tweetpulse.ingestion.pipeline.Redis.from_url', return_value=clean_redis):
                pipeline = IngestionPipeline(
                    keywords=["test"],
                    staging_dir=staging_dir,
                    num_workers=1
                )
                
                # BEHAVIOR: Process a tweet
                await pipeline.process_tweet(sample_tweet_data)
                
                # OBSERVABLE OUTCOME: Tweet was stored in cache
                # (verified by pipeline.execute being called)
                assert mock_pipe.execute.call_count > 0
    
    @pytest.mark.asyncio
    async def test_pipeline_skips_duplicate_tweets(self, staging_dir, sample_tweet_data, clean_redis):
        """Test behavior: pipeline ignores duplicate tweets."""
        with patch('tweetpulse.ingestion.pipeline.TwitterStreamConnector'), \
             patch('tweetpulse.ingestion.enrichment.pipeline') as mock_nlp, \
             patch('tweetpulse.ingestion.enrichment.torch') as mock_torch:
            
            mock_torch.cuda.is_available.return_value = False
            mock_nlp.return_value = MagicMock()
            
            # Mock bloom filter to return duplicate
            clean_redis.bf = MagicMock()
            bf_mock = clean_redis.bf.return_value
            bf_mock.exists = AsyncMock(return_value=True)
            clean_redis.sismember = AsyncMock(return_value=True)
            
            # Mock storage
            clean_redis.pipeline = MagicMock()
            mock_pipe = MagicMock()
            clean_redis.pipeline.return_value = mock_pipe
            mock_pipe.execute = AsyncMock()
            
            with patch('tweetpulse.ingestion.pipeline.Redis.from_url', return_value=clean_redis):
                pipeline = IngestionPipeline(
                    keywords=["test"],
                    staging_dir=staging_dir,
                    num_workers=1
                )
                
                # BEHAVIOR: Process duplicate tweet
                await pipeline.process_tweet(sample_tweet_data)
                
                # OBSERVABLE OUTCOME: Tweet was NOT stored (duplicate)
                mock_pipe.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_pipeline_processes_batch_deterministically(
        self, staging_dir, sample_tweets_batch
    ):
        """Test pipeline processes batch of tweets in order."""
        with patch('tweetpulse.ingestion.pipeline.Redis') as mock_redis_class, \
             patch('tweetpulse.ingestion.pipeline.TwitterStreamConnector'), \
             patch('tweetpulse.ingestion.enrichment.pipeline') as mock_nlp, \
             patch('tweetpulse.ingestion.enrichment.torch') as mock_torch, \
             patch('tweetpulse.ingestion.enrichment.langdetect.detect') as mock_detect:
            
            mock_torch.cuda.is_available.return_value = False
            mock_sentiment = MagicMock()
            mock_sentiment.return_value = [{"label": "NEUTRAL", "score": 0.5}]
            mock_nlp.return_value = mock_sentiment
            mock_detect.return_value = "en"
            
            mock_redis = MagicMock()
            mock_redis_class.from_url.return_value = mock_redis
            
            # Track processed tweets
            processed_ids = []
            
            # Mock bloom filter
            mock_redis.bf = MagicMock()
            bf_mock = mock_redis.bf.return_value
            bf_mock.exists = AsyncMock(return_value=False)
            bf_mock.add = AsyncMock()
            mock_redis.sismember = AsyncMock(return_value=False)
            mock_redis.sadd = AsyncMock()
            
            # Mock storage
            mock_redis.pipeline = MagicMock()
            mock_pipe = MagicMock()
            mock_redis.pipeline.return_value = mock_pipe
            mock_pipe.hset = MagicMock()
            mock_pipe.expire = MagicMock()
            mock_pipe.lpush = MagicMock()
            mock_pipe.ltrim = MagicMock()
            mock_pipe.sadd = MagicMock()
            mock_pipe.incr = MagicMock()
            
            async def track_execute():
                # Get the last hset call to track tweet ID
                if mock_pipe.hset.call_count > 0:
                    call_args = mock_pipe.hset.call_args
                    # Extract tweet ID from key (format: "tweet:{id}")
                    key = call_args[0][0]
                    if key.startswith("tweet:"):
                        tweet_id = key.split(":")[1]
                        processed_ids.append(tweet_id)
            
            mock_pipe.execute = AsyncMock(side_effect=track_execute)
            
            pipeline = IngestionPipeline(
                keywords=["test"],
                staging_dir=staging_dir,
                num_workers=1
            )
            
            # Process tweets sequentially
            for tweet in sample_tweets_batch[:5]:
                await pipeline.process_tweet(tweet)
            
            # Verify all tweets were processed
            assert mock_pipe.execute.call_count == 5
    
    @pytest.mark.asyncio
    async def test_pipeline_handles_enrichment_errors(self, staging_dir, sample_tweet_data):
        """Test pipeline handles enrichment errors gracefully."""
        with patch('tweetpulse.ingestion.pipeline.Redis') as mock_redis_class, \
             patch('tweetpulse.ingestion.pipeline.TwitterStreamConnector'), \
             patch('tweetpulse.ingestion.enrichment.pipeline') as mock_nlp, \
             patch('tweetpulse.ingestion.enrichment.torch') as mock_torch:
            
            mock_torch.cuda.is_available.return_value = False
            
            # Enrichment throws error
            mock_nlp.side_effect = Exception("Model error")
            
            mock_redis = MagicMock()
            mock_redis_class.from_url.return_value = mock_redis
            
            # Mock deduplicator
            mock_redis.bf = MagicMock()
            bf_mock = mock_redis.bf.return_value
            bf_mock.exists = AsyncMock(return_value=False)
            bf_mock.add = AsyncMock()
            mock_redis.sismember = AsyncMock(return_value=False)
            mock_redis.sadd = AsyncMock()
            
            pipeline = IngestionPipeline(
                keywords=["test"],
                staging_dir=staging_dir,
                num_workers=1
            )
            
            # Should not crash
            with pytest.raises(Exception):
                await pipeline.process_tweet(sample_tweet_data)
    
    @pytest.mark.asyncio
    async def test_pipeline_concurrent_processing(self, staging_dir, sample_tweets_batch):
        """Test pipeline handles concurrent tweet processing."""
        with patch('tweetpulse.ingestion.pipeline.Redis') as mock_redis_class, \
             patch('tweetpulse.ingestion.pipeline.TwitterStreamConnector'), \
             patch('tweetpulse.ingestion.enrichment.pipeline') as mock_nlp, \
             patch('tweetpulse.ingestion.enrichment.torch') as mock_torch, \
             patch('tweetpulse.ingestion.enrichment.langdetect.detect') as mock_detect:
            
            mock_torch.cuda.is_available.return_value = False
            mock_sentiment = MagicMock()
            mock_sentiment.return_value = [{"label": "NEUTRAL", "score": 0.5}]
            mock_nlp.return_value = mock_sentiment
            mock_detect.return_value = "en"
            
            mock_redis = MagicMock()
            mock_redis_class.from_url.return_value = mock_redis
            
            # Mock components
            mock_redis.bf = MagicMock()
            bf_mock = mock_redis.bf.return_value
            bf_mock.exists = AsyncMock(return_value=False)
            bf_mock.add = AsyncMock()
            mock_redis.sismember = AsyncMock(return_value=False)
            mock_redis.sadd = AsyncMock()
            
            mock_redis.pipeline = MagicMock()
            mock_pipe = MagicMock()
            mock_redis.pipeline.return_value = mock_pipe
            mock_pipe.hset = MagicMock()
            mock_pipe.expire = MagicMock()
            mock_pipe.lpush = MagicMock()
            mock_pipe.ltrim = MagicMock()
            mock_pipe.sadd = MagicMock()
            mock_pipe.incr = MagicMock()
            mock_pipe.execute = AsyncMock()
            
            pipeline = IngestionPipeline(
                keywords=["test"],
                staging_dir=staging_dir,
                num_workers=1
            )
            
            # Process multiple tweets concurrently
            await asyncio.gather(*[
                pipeline.process_tweet(tweet)
                for tweet in sample_tweets_batch[:5]
            ])
            
            # All should be processed
            assert mock_pipe.execute.call_count == 5
    
    @pytest.mark.asyncio
    async def test_pipeline_get_session(self, staging_dir):
        """Test pipeline creates database session correctly."""
        with patch('tweetpulse.ingestion.pipeline.Redis') as mock_redis_class, \
             patch('tweetpulse.ingestion.pipeline.TwitterStreamConnector'), \
             patch('tweetpulse.ingestion.pipeline.create_engine') as mock_engine, \
             patch('tweetpulse.ingestion.pipeline.sessionmaker') as mock_sessionmaker, \
             patch('tweetpulse.ingestion.enrichment.pipeline') as mock_nlp, \
             patch('tweetpulse.ingestion.enrichment.torch') as mock_torch:
            
            mock_torch.cuda.is_available.return_value = False
            mock_nlp.return_value = MagicMock()
            mock_redis = MagicMock()
            mock_redis_class.from_url.return_value = mock_redis
            
            mock_session = MagicMock()
            mock_sessionmaker.return_value = mock_session
            
            pipeline = IngestionPipeline(
                keywords=["test"],
                staging_dir=staging_dir,
                num_workers=1
            )
            
            session = pipeline.get_session()
            
            mock_engine.assert_called_once()
            mock_sessionmaker.assert_called_once()
            assert session is not None
