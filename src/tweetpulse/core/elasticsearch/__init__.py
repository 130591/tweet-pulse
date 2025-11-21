"""
ElasticSearch client and configuration
"""

from elasticsearch import AsyncElasticsearch
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ElasticClient:
  """ElasticSearch client wrapper"""

  def __init__(self, url: str = "http://localhost:9200"):
    """Initialize ElasticSearch client"""
    self.client = AsyncElasticsearch([url])
    self.indices_created = False

  async def ensure_indices(self):
    """Create indices if they don't exist"""
    if self.indices_created:
      return

    # Tweet index with proper mappings
    tweet_mapping = {
      "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "text": {"type": "text", "analyzer": "standard"},
            "author_id": {"type": "keyword"},
            "author_name": {"type": "keyword"},
            "created_at": {"type": "date"},
            "ingested_at": {"type": "date"},
            "processed_at": {"type": "date"},

            # Metrics
            "retweet_count": {"type": "integer"},
            "reply_count": {"type": "integer"},
            "like_count": {"type": "integer"},
            "quote_count": {"type": "integer"},

            # Analysis results
            "sentiment": {
                "type": "object",
                "properties": {
                    "label": {"type": "keyword"},
                    "score": {"type": "float"},
                    "confidence": {"type": "float"}
                }
            },

            "entities": {
                "type": "nested",
                "properties": {
                    "text": {"type": "keyword"},
                    "type": {"type": "keyword"},
                    "score": {"type": "float"}
                }
            },

            "keywords": {
                "type": "keyword"
            },

            "language": {"type": "keyword"},
            "location": {
                "type": "object",
                "properties": {
                    "country": {"type": "keyword"},
                    "city": {"type": "keyword"},
                    "coordinates": {"type": "geo_point"}
                }
            },

            # Metadata
            "source": {"type": "keyword"},
            "stream_key": {"type": "keyword"},
            "worker_id": {"type": "keyword"},
            "batch_id": {"type": "keyword"}
          }
      },
      "settings": {
          "number_of_shards": 2,
          "number_of_replicas": 0,
          "refresh_interval": "1s"
      }
    }

    # Create tweet index
    if not await self.client.indices.exists(index="tweets"):
      await self.client.indices.create(index="tweets", body=tweet_mapping)
      logger.info("Created 'tweets' index in ElasticSearch")

    # Create aggregations index for metrics
    agg_mapping = {
        "mappings": {
            "properties": {
                "timestamp": {"type": "date"},
                "interval": {"type": "keyword"},  # "hour", "day", "week"
                "keyword": {"type": "keyword"},
                "sentiment_summary": {
                    "type": "object",
                    "properties": {
                        "positive": {"type": "integer"},
                        "negative": {"type": "integer"},
                        "neutral": {"type": "integer"}
                    }
                },
                "total_tweets": {"type": "integer"},
                "total_reach": {"type": "long"},
                "top_entities": {
                    "type": "nested",
                    "properties": {
                        "text": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "count": {"type": "integer"}
                    }
                }
            }
        }
    }

    if not await self.client.indices.exists(index="tweet_aggregations"):
      await self.client.indices.create(index="tweet_aggregations", body=agg_mapping)
      logger.info("Created 'tweet_aggregations' index in ElasticSearch")

    self.indices_created = True

  async def index_tweet(self, tweet: dict, index: str = "tweets"):
    """Index a single tweet"""
    await self.ensure_indices()
    return await self.client.index(
        index=index,
        id=tweet.get("id"),
        body=tweet
    )

  async def bulk_index_tweets(self, tweets: list, index: str = "tweets"):
    """Bulk index tweets"""
    await self.ensure_indices()

    # Prepare bulk operations
    operations = []
    for tweet in tweets:
      operations.append({"index": {"_index": index, "_id": tweet.get("id")}})
      operations.append(tweet)

    if operations:
      response = await self.client.bulk(body=operations)
      logger.info(f"Bulk indexed {len(tweets)} tweets")
      return response

  async def search_tweets(self, query: dict, index: str = "tweets"):
    """Search tweets with query"""
    return await self.client.search(index=index, body=query)

  async def aggregate_sentiment(self, keyword: str, time_range: str = "1h"):
    """Aggregate sentiment for a keyword"""
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"keywords": keyword}},
                    {"range": {"created_at": {"gte": f"now-{time_range}"}}}
                ]
            }
        },
        "aggs": {
            "sentiment_distribution": {
                "terms": {
                    "field": "sentiment.label"
                }
            },
            "avg_confidence": {
                "avg": {
                    "field": "sentiment.confidence"
                }
            }
        }
    }

    return await self.client.search(index="tweets", body=query)

  async def close(self):
    """Close ElasticSearch client"""
    await self.client.close()


# Global client instance
_elastic_client: Optional[ElasticClient] = None


def get_elastic_client(url: str = None) -> ElasticClient:
  """Get or create ElasticSearch client"""
  global _elastic_client

  if _elastic_client is None:
    from tweetpulse.core.config import get_settings
    settings = get_settings()
    es_url = url or getattr(
        settings,
        'ELASTICSEARCH_URL',
        'http://localhost:9200')
    _elastic_client = ElasticClient(es_url)

  return _elastic_client
