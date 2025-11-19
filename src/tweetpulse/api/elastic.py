"""
ElasticSearch API endpoints
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from tweetpulse.core.elasticsearch.client import get_elastic_client

router = APIRouter(prefix="/api/elastic", tags=["elasticsearch"])


@router.get("/search")
async def search_tweets(
    q: str = Query(..., description="Search query"),
    size: int = Query(10, ge=1, le=100, description="Number of results"),
    from_: int = Query(0, ge=0, alias="from", description="Offset for pagination"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (positive/negative/neutral)"),
    time_range: Optional[str] = Query("24h", description="Time range (e.g., 1h, 24h, 7d)")
):
    """
    Search tweets in ElasticSearch
    """
    try:
        elastic = get_elastic_client()
        
        # Build query
        must_conditions = []
        
        # Text search
        must_conditions.append({
            "multi_match": {
                "query": q,
                "fields": ["text^2", "keywords", "entities.text"],
                "type": "best_fields"
            }
        })
        
        # Time range filter
        if time_range:
            must_conditions.append({
                "range": {
                    "created_at": {
                        "gte": f"now-{time_range}"
                    }
                }
            })
        
        # Sentiment filter
        if sentiment:
            must_conditions.append({
                "term": {
                    "sentiment.label": sentiment.lower()
                }
            })
        
        # Construct ElasticSearch query
        es_query = {
            "query": {
                "bool": {
                    "must": must_conditions
                }
            },
            "sort": [
                {"_score": "desc"},
                {"created_at": "desc"}
            ],
            "size": size,
            "from": from_,
            "highlight": {
                "fields": {
                    "text": {}
                }
            }
        }
        
        # Execute search
        result = await elastic.search_tweets(es_query)
        
        # Format response
        hits = result.get("hits", {})
        tweets = []
        
        for hit in hits.get("hits", []):
            tweet = hit["_source"]
            tweet["_score"] = hit["_score"]
            
            # Add highlights if available
            if "highlight" in hit:
                tweet["_highlights"] = hit["highlight"].get("text", [])
            
            tweets.append(tweet)
        
        return {
            "total": hits.get("total", {}).get("value", 0),
            "tweets": tweets,
            "from": from_,
            "size": size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/analytics/sentiment")
async def sentiment_analytics(
    keyword: Optional[str] = Query(None, description="Filter by keyword"),
    time_range: str = Query("24h", description="Time range (e.g., 1h, 24h, 7d)")
):
    """
    Get sentiment analytics from ElasticSearch
    """
    try:
        elastic = get_elastic_client()
        
        # Build query
        query_conditions = []
        
        if keyword:
            query_conditions.append({
                "match": {"keywords": keyword}
            })
        
        query_conditions.append({
            "range": {
                "created_at": {
                    "gte": f"now-{time_range}"
                }
            }
        })
        
        # Aggregation query
        es_query = {
            "query": {
                "bool": {
                    "must": query_conditions
                } if query_conditions else {"match_all": {}}
            },
            "size": 0,  # We only want aggregations
            "aggs": {
                "sentiment_distribution": {
                    "terms": {
                        "field": "sentiment.label",
                        "size": 10
                    }
                },
                "avg_confidence": {
                    "avg": {
                        "field": "sentiment.confidence"
                    }
                },
                "sentiment_over_time": {
                    "date_histogram": {
                        "field": "created_at",
                        "calendar_interval": "1h" if time_range in ["1h", "6h", "12h", "24h"] else "1d",
                        "format": "yyyy-MM-dd HH:mm:ss"
                    },
                    "aggs": {
                        "sentiments": {
                            "terms": {
                                "field": "sentiment.label"
                            }
                        }
                    }
                },
                "total_reach": {
                    "sum": {
                        "script": {
                            "source": "doc['retweet_count'].value + doc['reply_count'].value + doc['like_count'].value"
                        }
                    }
                }
            }
        }
        
        # Execute query
        result = await elastic.search_tweets(es_query)
        
        # Format response
        aggs = result.get("aggregations", {})
        
        # Process sentiment distribution
        sentiment_dist = {}
        for bucket in aggs.get("sentiment_distribution", {}).get("buckets", []):
            sentiment_dist[bucket["key"]] = bucket["doc_count"]
        
        # Process time series
        time_series = []
        for bucket in aggs.get("sentiment_over_time", {}).get("buckets", []):
            point = {
                "timestamp": bucket["key_as_string"],
                "total": bucket["doc_count"],
                "sentiments": {}
            }
            
            for sent_bucket in bucket.get("sentiments", {}).get("buckets", []):
                point["sentiments"][sent_bucket["key"]] = sent_bucket["doc_count"]
            
            time_series.append(point)
        
        return {
            "keyword": keyword,
            "time_range": time_range,
            "sentiment_distribution": sentiment_dist,
            "avg_confidence": aggs.get("avg_confidence", {}).get("value"),
            "total_reach": int(aggs.get("total_reach", {}).get("value", 0)),
            "time_series": time_series
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")


@router.get("/analytics/entities")
async def entity_analytics(
    entity_type: Optional[str] = Query(None, description="Entity type (PERSON, ORG, LOC)"),
    time_range: str = Query("24h", description="Time range"),
    size: int = Query(10, ge=1, le=50, description="Number of top entities")
):
    """
    Get top entities from tweets
    """
    try:
        elastic = get_elastic_client()
        
        # Build query
        es_query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"created_at": {"gte": f"now-{time_range}"}}},
                        {"exists": {"field": "entities"}}
                    ]
                }
            },
            "size": 0,
            "aggs": {
                "entities": {
                    "nested": {
                        "path": "entities"
                    },
                    "aggs": {
                        "filtered": {
                            "filter": {
                                "term": {"entities.type": entity_type}
                            } if entity_type else {"match_all": {}},
                            "aggs": {
                                "top_entities": {
                                    "terms": {
                                        "field": "entities.text",
                                        "size": size
                                    },
                                    "aggs": {
                                        "avg_score": {
                                            "avg": {
                                                "field": "entities.score"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Execute query
        result = await elastic.search_tweets(es_query)
        
        # Format response
        entities = []
        nested_agg = result.get("aggregations", {}).get("entities", {})
        filtered_agg = nested_agg.get("filtered", {})
        
        for bucket in filtered_agg.get("top_entities", {}).get("buckets", []):
            entities.append({
                "text": bucket["key"],
                "count": bucket["doc_count"],
                "avg_score": bucket.get("avg_score", {}).get("value")
            })
        
        return {
            "entity_type": entity_type,
            "time_range": time_range,
            "entities": entities
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Entity analytics failed: {str(e)}")


@router.get("/stats")
async def get_elasticsearch_stats():
    """
    Get ElasticSearch cluster and index statistics
    """
    try:
        elastic = get_elastic_client()
        
        # Get index stats
        stats = await elastic.client.indices.stats(index="tweets")
        
        # Get cluster health
        health = await elastic.client.cluster.health()
        
        return {
            "cluster_health": health,
            "index_stats": {
                "total_docs": stats["indices"]["tweets"]["total"]["docs"]["count"],
                "index_size": stats["indices"]["tweets"]["total"]["store"]["size_in_bytes"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")
