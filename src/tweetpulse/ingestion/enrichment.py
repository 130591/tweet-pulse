import asyncio
import re
from datetime import datetime
from typing import List

import torch
import langdetect
from transformers import pipeline

class TweetEnricher:
  def __init__(self):
    self.sentiment_model = pipeline(
      "sentiment-analysis",
      model="distilbert-base-uncased-finetuned-sst-2-english",
      device=0 if torch.cuda.is_available() else -1
    )
  
  async def enrich(self, tweet_data: dict) -> dict:
    text = tweet_data['text']
    cleaned_text = self._clean_text(text)
    
    try:
      language = langdetect.detect(cleaned_text)
    except:
      language = "unknown"
    if language == "en" and len(cleaned_text) > 10:
      sentiment = self.sentiment_model(cleaned_text[:512])[0]
    else:
      sentiment = {"label": "NEUTRAL", "score": 0.5}
    return {
      **tweet_data,
      "cleaned_text": cleaned_text,
          "language": language,
          "sentiment": sentiment['label'].lower(),
          "confidence": sentiment['score'],
          "enriched_at": datetime.utcnow().isoformat(),
      }
  
  def _clean_text(self, text: str) -> str:
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

class BatchEnricher:
  
  def __init__(self, batch_size: int = 32):
    self.enricher = TweetEnricher()
    self.batch = []
    self.batch_size = batch_size
  
  async def add(self, tweet_data: dict):
    self.batch.append(tweet_data)
    
    if len(self.batch) >= self.batch_size:
      await self.flush()
  
  async def flush(self):
    if not self.batch:
      return []
      
    enriched = await asyncio.gather(*[
      self.enricher.enrich(t) for t in self.batch
    ])
    
    self.batch = []
    return enriched