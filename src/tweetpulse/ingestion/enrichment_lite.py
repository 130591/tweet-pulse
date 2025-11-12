"""
Lightweight sentiment analysis using VADER instead of PyTorch/Transformers.
VADER is optimized for social media text and is ~1MB vs PyTorch ~3GB.
"""
import asyncio
import re
from datetime import datetime
from typing import List, Optional, Dict, Any

import langdetect
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class TweetEnricher:
    """Lightweight tweet enricher using VADER for sentiment analysis."""
    
    def __init__(self, sentiment_analyzer: Optional[SentimentIntensityAnalyzer] = None):
        """Initialize with optional sentiment analyzer injection."""
        self.sentiment_analyzer = sentiment_analyzer or SentimentIntensityAnalyzer()
    
    async def enrich(self, tweet_data: dict) -> dict:
        """Enrich tweet with sentiment, language, and cleaned text."""
        text = tweet_data['text']
        cleaned_text = self._clean_text(text)
        
        # Detect language
        try:
            language = langdetect.detect(cleaned_text)
        except:
            language = "unknown"
        
        # Analyze sentiment using VADER
        if len(cleaned_text) > 10:
            sentiment_scores = self.sentiment_analyzer.polarity_scores(cleaned_text)
            sentiment_label, confidence = self._interpret_vader_scores(sentiment_scores)
        else:
            sentiment_label = "neutral"
            confidence = 0.5
        
        return {
					**tweet_data,
					"cleaned_text": cleaned_text,
					"language": language,
					"sentiment": sentiment_label,
					"confidence": confidence,
					"enriched_at": datetime.utcnow().isoformat(),
        }
    
    def _clean_text(self, text: str) -> str:
        """Remove URLs, mentions, and hashtags from text."""
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#\w+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _interpret_vader_scores(self, scores: dict) -> tuple[str, float]:
        """
        Convert VADER compound score to sentiment label and confidence.
        
        VADER compound score ranges from -1 (most negative) to +1 (most positive).
        Standard thresholds:
        - compound >= 0.05: positive
        - compound <= -0.05: negative
        - else: neutral
        """
        compound = scores['compound']
        
        if compound >= 0.05:
            return "positive", abs(compound)
        elif compound <= -0.05:
            return "negative", abs(compound)
        else:
            return "neutral", 1 - abs(compound)


class BatchEnricher:
	"""Batch processor for tweet enrichment."""
	
	def __init__(self, batch_size: int = 32, enricher: Optional[TweetEnricher] = None):
			"""Initialize with optional enricher injection."""
			self.enricher = enricher or TweetEnricher()
			self.batch = []
			self.batch_size = batch_size
	
	async def add(self, tweet_data: dict):
			"""Add tweet to batch and flush if batch is full."""
			self.batch.append(tweet_data)
			
			if len(self.batch) >= self.batch_size:
					await self.flush()
	
	async def flush(self):
			"""Process all tweets in batch."""
			if not self.batch:
					return []
			
			enriched = await asyncio.gather(*[
					self.enricher.enrich(t) for t in self.batch
			])
			
			self.batch = []
			return enriched
