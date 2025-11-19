"""
Tweet Pulse - Twitter Stream Processing Pipeline

A comprehensive system for ingesting, processing, enriching, and storing
Twitter data streams with real-time deduplication and sentiment analysis.
"""

__version__ = "1.0.0"
__author__ = "Tweet Pulse Team"

from .ingestion import (
    IngestionPipeline,
    TwitterStreamConnector,
    StreamConsumer,
    BloomDeduplicator,
    TweetEnricher,
    BatchEnricher,
    Storage,
    BatchWriter,
)
from .core.distributed import (
    RedisLock,
    DistributedLockManager,
)

__all__ = [
    "IngestionPipeline",
    "TwitterStreamConnector",
    "StreamConsumer",
    "BloomDeduplicator",
    "TweetEnricher",
    "BatchEnricher",
    "Storage",
    "BatchWriter",
    "RedisLock",
    "DistributedLockManager",
]
