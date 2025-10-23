class Processor:
  def __init__(self, redis: Redis):
    self.redis = redis
    self.deduplicator = BloomDeduplicator(redis, "dedup:bloom")
    self.repository = TweetRepository(redis)
    self.sentiment_analyzer = SentimentAnalyzer()