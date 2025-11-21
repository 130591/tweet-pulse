from typing import Dict, Any
from ....models.tweet import Tweet

class TweetDocumentMapper:
  """
  Responsible for converting Tweet domain models into Elasticsearch documents.
  """
  
  @staticmethod
  def to_document(tweet: Tweet) -> Dict[str, Any]:
    """Converts a Tweet model to an Elasticsearch document."""
    
    # Handle optional relationships
    author_data = {}
    if tweet.profile:
      author_data = {
        "id": str(tweet.profile.id),
        "username": tweet.profile.username,
        "name": tweet.profile.name,
        "followers_count": 0  # Placeholder: followers_count is in ProfileSnapshot
      }

    sentiment_data = {}
    if tweet.sentiment:
      sentiment_data = {
        "label": tweet.sentiment.label,
        "score": float(tweet.sentiment.score),
        "model": tweet.sentiment.model
      }

    entities_data = []
    if tweet.entities:
      for entity in tweet.entities:
        entities_data.append({
          "text": entity.text,
          "type": entity.type,
          "score": float(entity.score) if entity.score else None
        })

    hashtags_data = [h.tag for h in tweet.hashtags] if tweet.hashtags else []
    mentions_data = [m.mentioned_profile.username for m in tweet.mentions if m.mentioned_profile] if tweet.mentions else []

    return {
      "id": str(tweet.id),
      "content": tweet.content,
      "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
      "ingested_at": tweet.ingested_at.isoformat() if tweet.ingested_at else None,
      "language": tweet.language,
      "author": author_data,
      "metrics": {
        "retweet_count": tweet.retweet_count,
        "reply_count": tweet.reply_count,
        "like_count": tweet.like_count,
        "quote_count": tweet.quote_count,
        "total_engagement": (tweet.retweet_count or 0) + (tweet.reply_count or 0) + (tweet.like_count or 0) + (tweet.quote_count or 0)
      },
      "sentiment": sentiment_data,
      "entities": entities_data,
      "hashtags": hashtags_data,
      "mentions": mentions_data
    }
