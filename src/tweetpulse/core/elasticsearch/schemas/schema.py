TWEET_INDEX_MAPPING = {
  "mappings": {
    "properties": {
        "id": {"type": "keyword"},
        "content": {
          "type": "text",
          "analyzer": "standard",
          "fields": {
            "portuguese": {"type": "text", "analyzer": "portuguese"},
            "english": {"type": "text", "analyzer": "english"},
            "keyword": {"type": "keyword", "ignore_above": 256}
          }
        },
        "created_at": {"type": "date"},
        "ingested_at": {"type": "date"},
        "language": {"type": "keyword"},
        "author": {
          "properties": {
            "id": {"type": "keyword"},
            "username": {"type": "keyword"},
            "name": {"type": "text"},
            "followers_count": {"type": "integer"}
          }
        },
        "metrics": {
          "properties": {
            "retweet_count": {"type": "integer"},
            "reply_count": {"type": "integer"},
            "like_count": {"type": "integer"},
            "quote_count": {"type": "integer"},
            "total_engagement": {"type": "integer"}
          }
        },
        "sentiment": {
          "properties": {
            "label": {"type": "keyword"},
            "score": {"type": "float"},
            "model": {"type": "keyword"}
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
        "hashtags": {"type": "keyword"},
        "mentions": {"type": "keyword"}
    }
  }
}
