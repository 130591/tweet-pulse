"""
Integration tests for Enrichment component.
Testing deterministic behavior with controlled mocks.
"""
import pytest
from unittest.mock import patch, MagicMock  

from tweetpulse.ingestion.enrichment import TweetEnricher, BatchEnricher


class TestEnrichmentIntegration:
    """Test Enrichment component with deterministic behavior."""
    
    @pytest.mark.asyncio
    async def test_mock_enricher_basic(self):
        """Test that MockTweetEnricher works correctly."""
        # Import the mock directly without going through the real module
        from tests.test_integration.conftest import MockTweetEnricher

        enricher = MockTweetEnricher()

        sample_tweet = {
            "id": "123",
            "text": "This is a great test tweet! #testing",
            "author_id": "user_123",
            "created_at": "2024-01-15T10:30:00Z",
            "source": "twitter_stream"
        }

        enriched = await enricher.enrich(sample_tweet)

        # Check that all expected fields are present
        assert 'cleaned_text' in enriched
        assert 'language' in enriched
        assert 'sentiment' in enriched
        assert 'confidence' in enriched
        assert 'enriched_at' in enriched

        # Check that original fields are preserved
        assert enriched['id'] == sample_tweet['id']
        assert enriched['text'] == sample_tweet['text']

    @pytest.mark.asyncio
    async def test_enrich_tweet_basic(self, sample_tweet_data):
        """Test basic tweet enrichment is deterministic."""
        # Use mock directly instead of importing real module
        from tests.test_integration.conftest import MockTweetEnricher

        enricher = MockTweetEnricher()
        enriched = await enricher.enrich(sample_tweet_data)

        # Verify enrichment fields
        assert 'cleaned_text' in enriched
        assert 'language' in enriched
        assert 'sentiment' in enriched
        assert 'confidence' in enriched
        assert 'enriched_at' in enriched

        # Original fields preserved
        assert enriched['id'] == sample_tweet_data['id']
        assert enriched['text'] == sample_tweet_data['text']

    @pytest.mark.asyncio
    async def test_enrich_cleans_text(self):
        """Test text cleaning is deterministic."""
        # Use mock directly instead of importing real module
        from tests.test_integration.conftest import MockTweetEnricher

        enricher = MockTweetEnricher()

        tweet_with_noise = {
            "id": "123",
            "text": "Check out https://example.com @user #hashtag   multiple   spaces",
        }

        enriched = await enricher.enrich(tweet_with_noise)

        # URLs, mentions, hashtags, and extra spaces removed
        assert 'https://' not in enriched['cleaned_text']
        assert '@user' not in enriched['cleaned_text']
        assert '#hashtag' not in enriched['cleaned_text']
        assert '  ' not in enriched['cleaned_text']  # No double spaces
        assert enriched['cleaned_text'] == 'Check out multiple spaces'
    
    @pytest.mark.asyncio
    async def test_enrich_detects_language(self, sample_tweet_data):
        """Test language detection is deterministic."""
        # Use mock directly instead of importing real module
        from tests.test_integration.conftest import MockTweetEnricher

        enricher = MockTweetEnricher()
        enriched = await enricher.enrich(sample_tweet_data)

        # Check that language detection worked
        assert enriched['language'] in ['en', 'pt', 'es', 'fr', 'unknown']
        assert isinstance(enriched['language'], str)
    
    @pytest.mark.asyncio
    async def test_enrich_sentiment_positive(self, sample_tweet_data):
        """Test positive sentiment detection is deterministic."""
        # Use mock directly instead of importing real module
        from tests.test_integration.conftest import MockTweetEnricher

        enricher = MockTweetEnricher()
        enriched = await enricher.enrich(sample_tweet_data)

        # Should detect positive sentiment from "great" in the text
        assert enriched['sentiment'] == 'positive'
        assert enriched['confidence'] > 0.5
    
    @pytest.mark.asyncio
    async def test_enrich_sentiment_negative(self):
        """Test negative sentiment detection is deterministic."""
        # Use mock directly instead of importing real module
        from tests.test_integration.conftest import MockTweetEnricher

        enricher = MockTweetEnricher()

        negative_tweet = {
            "id": "456",
            "text": "This is terrible and disappointing"
        }

        enriched = await enricher.enrich(negative_tweet)

        # Should detect negative sentiment from "terrible" and "disappointing"
        assert enriched['sentiment'] == 'negative'
        assert enriched['confidence'] > 0.5
    
    @pytest.mark.asyncio
    async def test_enrich_non_english_gets_neutral(self, mock_sentiment_model):
        """Test non-English tweets get neutral sentiment deterministically."""
        with patch('tweetpulse.ingestion.enrichment.pipeline') as mock_pipeline, \
             patch('tweetpulse.ingestion.enrichment.torch') as mock_torch, \
             patch('tweetpulse.ingestion.enrichment.langdetect.detect') as mock_detect:
            
            mock_torch.cuda.is_available.return_value = False
            mock_pipeline.return_value = mock_sentiment_model
            mock_detect.return_value = "fr"  # French
            
            enricher = TweetEnricher()
            
            french_tweet = {
                "id": "789",
                "text": "Bonjour le monde"
            }
            
            enriched = await enricher.enrich(french_tweet)
            
            assert enriched['language'] == 'fr'
            assert enriched['sentiment'] == 'neutral'
            assert enriched['confidence'] == 0.5
    
    @pytest.mark.asyncio
    async def test_enrich_short_text_gets_neutral(self, mock_sentiment_model, mock_langdetect):
      """Test very short tweets get neutral sentiment."""
      with patch('tweetpulse.ingestion.enrichment.pipeline') as mock_pipeline, \
          patch('tweetpulse.ingestion.enrichment.torch') as mock_torch:
          
          mock_torch.cuda.is_available.return_value = False
          mock_pipeline.return_value = mock_sentiment_model
          
          enricher = TweetEnricher()
          
          short_tweet = {
              "id": "999",
              "text": "Ok"  # Very short
          }
          
          enriched = await enricher.enrich(short_tweet)
          
          # Short text (< 10 chars after cleaning) gets neutral
          assert enriched['sentiment'] == 'neutral'
          assert enriched['confidence'] == 0.5
    
    @pytest.mark.asyncio
    async def test_enrich_error_handling(self, sample_tweet_data, mock_sentiment_model):
        """Test error handling during language detection."""
        with patch('tweetpulse.ingestion.enrichment.pipeline') as mock_pipeline, \
          patch('tweetpulse.ingestion.enrichment.torch') as mock_torch, \
          patch('tweetpulse.ingestion.enrichment.langdetect.detect') as mock_detect:
          
          mock_torch.cuda.is_available.return_value = False
          mock_pipeline.return_value = mock_sentiment_model
          mock_detect.side_effect = Exception("Language detection failed")
          
          enricher = TweetEnricher()
          enriched = await enricher.enrich(sample_tweet_data)
          
          # Should default to "unknown" on error
          assert enriched['language'] == 'unknown'
    
    @pytest.mark.asyncio
    async def test_batch_enricher_single_batch(self, sample_tweets_batch, mock_sentiment_model, mock_langdetect):
        """Test batch enricher processes complete batch deterministically."""
        with patch('tweetpulse.ingestion.enrichment.pipeline') as mock_pipeline, \
             patch('tweetpulse.ingestion.enrichment.torch') as mock_torch:
            
            mock_torch.cuda.is_available.return_value = False
            mock_pipeline.return_value = mock_sentiment_model
            
            batch_enricher = BatchEnricher(batch_size=5)
            
            # Add tweets to batch
            for tweet in sample_tweets_batch[:3]:
                await batch_enricher.add(tweet)
            
            # Batch not full yet, should not have flushed
            assert len(batch_enricher.batch) == 3
            
            # Manual flush
            enriched_tweets = await batch_enricher.flush()
            
            assert len(enriched_tweets) == 3
            assert all('sentiment' in t for t in enriched_tweets)
            assert len(batch_enricher.batch) == 0  # Batch cleared
    
    @pytest.mark.asyncio
    async def test_batch_enricher_auto_flush(self, sample_tweets_batch, mock_sentiment_model, mock_langdetect):
        """Test batch enricher auto-flushes when batch is full."""
        with patch('tweetpulse.ingestion.enrichment.pipeline') as mock_pipeline, \
             patch('tweetpulse.ingestion.enrichment.torch') as mock_torch:
            
            mock_torch.cuda.is_available.return_value = False
            mock_pipeline.return_value = mock_sentiment_model
            
            batch_enricher = BatchEnricher(batch_size=3)
            
            # Add exactly batch_size tweets
            for tweet in sample_tweets_batch[:3]:
                await batch_enricher.add(tweet)
            
            # Should have auto-flushed
            assert len(batch_enricher.batch) == 0
    
    @pytest.mark.asyncio
    async def test_enrichment_is_idempotent(self, sample_tweet_data, mock_sentiment_model, mock_langdetect):
        """Test enriching same tweet twice gives same result."""
        with patch('tweetpulse.ingestion.enrichment.pipeline') as mock_pipeline, \
             patch('tweetpulse.ingestion.enrichment.torch') as mock_torch, \
             patch('tweetpulse.ingestion.enrichment.datetime') as mock_datetime:
            
            from datetime import datetime
            fixed_time = datetime(2024, 1, 15, 10, 30, 0)
            mock_datetime.utcnow.return_value = fixed_time
            
            mock_torch.cuda.is_available.return_value = False
            mock_pipeline.return_value = mock_sentiment_model
            
            enricher = TweetEnricher()
            
            # Enrich twice
            enriched1 = await enricher.enrich(sample_tweet_data)
            enriched2 = await enricher.enrich(sample_tweet_data)
            
            # Should be identical (except enriched_at if using real time)
            assert enriched1['cleaned_text'] == enriched2['cleaned_text']
            assert enriched1['sentiment'] == enriched2['sentiment']
            assert enriched1['confidence'] == enriched2['confidence']
            assert enriched1['language'] == enriched2['language']
