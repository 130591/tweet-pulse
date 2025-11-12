from .pipeline import IngestionPipeline
from .connector import TwitterStreamConnector
from .consumer import StreamConsumer
from .deduplication import BloomDeduplicator
from .enrichment_factory import (
    create_enricher,
    create_batch_enricher,
    get_enricher_info,
)
from .storage import Storage
from .batch_writer import BatchWriter

# For backward compatibility, import from factory
# This will automatically select the right version based on environment
TweetEnricher = create_enricher
BatchEnricher = create_batch_enricher

__all__ = [
  "IngestionPipeline",
  "TwitterStreamConnector",
  "StreamConsumer",
  "BloomDeduplicator",
  "TweetEnricher",
  "BatchEnricher",
  "create_enricher",
  "create_batch_enricher",
  "get_enricher_info",
  "Storage",
  "BatchWriter",
]

__version__ = "1.0.0"