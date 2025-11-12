"""
Tests for lightweight sentiment analysis using VADER.
"""
import pytest
from tweetpulse.ingestion.enrichment_lite import TweetEnricher, BatchEnricher


class TestTweetEnricherLite:
    """Test suite for lightweight TweetEnricher."""
    
    @pytest.fixture
    def enricher(self):
        """Create a TweetEnricher instance."""
        return TweetEnricher()
    
    @pytest.mark.asyncio
    async def test_enrich_positive_tweet(self, enricher):
        """Test enrichment of a positive tweet."""
        tweet = {
            "id": "123",
            "text": "I love this amazing product! It's fantastic! 😊",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        result = await enricher.enrich(tweet)
        
        assert result["sentiment"] == "positive"
        assert result["confidence"] > 0.5
        assert "cleaned_text" in result
        assert "language" in result
        assert "enriched_at" in result
    
    @pytest.mark.asyncio
    async def test_enrich_negative_tweet(self, enricher):
        """Test enrichment of a negative tweet."""
        tweet = {
            "id": "124",
            "text": "This is terrible! I hate it! Worst experience ever! 😡",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        result = await enricher.enrich(tweet)
        
        assert result["sentiment"] == "negative"
        assert result["confidence"] > 0.5
    
    @pytest.mark.asyncio
    async def test_enrich_neutral_tweet(self, enricher):
        """Test enrichment of a neutral tweet."""
        tweet = {
            "id": "125",
            "text": "The weather is okay today.",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        result = await enricher.enrich(tweet)
        
        assert result["sentiment"] == "neutral"
    
    @pytest.mark.asyncio
    async def test_clean_text_removes_urls(self, enricher):
        """Test that URLs are removed from text."""
        tweet = {
            "id": "126",
            "text": "Check this out https://example.com great stuff!",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        result = await enricher.enrich(tweet)
        
        assert "https://example.com" not in result["cleaned_text"]
        assert "great stuff" in result["cleaned_text"]
    
    @pytest.mark.asyncio
    async def test_clean_text_removes_mentions(self, enricher):
        """Test that mentions are removed from text."""
        tweet = {
            "id": "127",
            "text": "@user this is a great tweet!",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        result = await enricher.enrich(tweet)
        
        assert "@user" not in result["cleaned_text"]
        assert "great tweet" in result["cleaned_text"]
    
    @pytest.mark.asyncio
    async def test_clean_text_removes_hashtags(self, enricher):
        """Test that hashtags are removed from text."""
        tweet = {
            "id": "128",
            "text": "This is #awesome #python code!",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        result = await enricher.enrich(tweet)
        
        assert "#awesome" not in result["cleaned_text"]
        assert "#python" not in result["cleaned_text"]
    
    @pytest.mark.asyncio
    async def test_short_text_neutral(self, enricher):
        """Test that very short text defaults to neutral."""
        tweet = {
            "id": "129",
            "text": "ok",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        result = await enricher.enrich(tweet)
        
        assert result["sentiment"] == "neutral"
        assert result["confidence"] == 0.5


class TestBatchEnricherLite:
    """Test suite for BatchEnricher with lite enricher."""
    
    @pytest.fixture
    def batch_enricher(self):
        """Create a BatchEnricher instance."""
        return BatchEnricher(batch_size=2)
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, batch_enricher):
        """Test batch processing of tweets."""
        tweets = [
            {"id": "1", "text": "Great product! Love it!", "created_at": "2024-01-01T00:00:00Z"},
            {"id": "2", "text": "Terrible experience!", "created_at": "2024-01-01T00:00:00Z"},
        ]
        
        # Add tweets (should auto-flush at batch_size)
        for tweet in tweets:
            await batch_enricher.add(tweet)
        
        # Batch should be empty after auto-flush
        assert len(batch_enricher.batch) == 0
    
    @pytest.mark.asyncio
    async def test_manual_flush(self, batch_enricher):
        """Test manual flush of batch."""
        tweet = {"id": "1", "text": "Good stuff!", "created_at": "2024-01-01T00:00:00Z"}
        
        await batch_enricher.add(tweet)
        assert len(batch_enricher.batch) == 1
        
        results = await batch_enricher.flush()
        assert len(results) == 1
        assert results[0]["sentiment"] in ["positive", "neutral", "negative"]
        assert len(batch_enricher.batch) == 0
    
    @pytest.mark.asyncio
    async def test_empty_flush(self, batch_enricher):
        """Test flushing empty batch."""
        results = await batch_enricher.flush()
        assert results == []


def test_vader_scores_interpretation():
    """Test VADER score interpretation logic."""
    enricher = TweetEnricher()
    
    # Positive
    label, conf = enricher._interpret_vader_scores({"compound": 0.8})
    assert label == "positive"
    assert conf == 0.8
    
    # Negative
    label, conf = enricher._interpret_vader_scores({"compound": -0.8})
    assert label == "negative"
    assert conf == 0.8
    
    # Neutral
    label, conf = enricher._interpret_vader_scores({"compound": 0.02})
    assert label == "neutral"
    assert conf > 0.9  # 1 - abs(0.02)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
