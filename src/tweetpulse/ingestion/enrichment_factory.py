"""
Factory for creating the appropriate TweetEnricher based on environment.
Automatically selects:
- Lite version (VADER) for development
- Full version (PyTorch/Transformers) for production
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def create_enricher(force_lite: Optional[bool] = None):
  """
  Create the appropriate TweetEnricher based on environment.
  
  Priority order:
  1. force_lite parameter (if provided)
  2. USE_LITE_ENRICHMENT environment variable
  3. ENVIRONMENT variable (development/production)
  4. Fallback to lite if PyTorch not available
  
  Args:
      force_lite: If True, force lite version. If False, force full version.
                  If None, auto-detect based on environment.
  
  Returns:
      TweetEnricher instance (either lite or full version)
  """
  
  # Check if forced
  if force_lite is not None:
      use_lite = force_lite
      reason = "forced parameter"
  else:
      # Check USE_LITE_ENRICHMENT env var
      use_lite_env = os.getenv("USE_LITE_ENRICHMENT", "").lower()
      
      if use_lite_env in ("1", "true", "yes"):
          use_lite = True
          reason = "USE_LITE_ENRICHMENT=1"
      elif use_lite_env in ("0", "false", "no"):
          use_lite = False
          reason = "USE_LITE_ENRICHMENT=0"
      else:
          # Check ENVIRONMENT variable
          environment = os.getenv("ENVIRONMENT", "development").lower()
          
          if environment in ("development", "dev", "local"):
              use_lite = True
              reason = f"ENVIRONMENT={environment}"
          elif environment in ("production", "prod", "staging"):
              use_lite = False
              reason = f"ENVIRONMENT={environment}"
          else:
              # Default to lite for unknown environments
              use_lite = True
              reason = "default (unknown environment)"
    
    # Try to import the requested version
  if use_lite:
      try:
          from .enrichment_lite import TweetEnricher
          logger.info(f"✅ Using LITE enricher (VADER) - {reason}")
          return TweetEnricher()
      except ImportError as e:
          logger.error(f"❌ Failed to import lite enricher: {e}")
          logger.info("⚠️  Falling back to full enricher...")
          use_lite = False
    
  if not use_lite:
      try:
          from .enrichment import TweetEnricher
          logger.info(f"✅ Using FULL enricher (PyTorch/Transformers) - {reason}")
          return TweetEnricher()
      except ImportError as e:
          logger.error(f"❌ Failed to import full enricher: {e}")
          logger.info("⚠️  Falling back to lite enricher...")
          try:
              from .enrichment_lite import TweetEnricher
              logger.warning("⚠️  Using LITE enricher as fallback")
              return TweetEnricher()
          except ImportError as e2:
              logger.error(f"❌ Failed to import any enricher: {e2}")
              raise ImportError(
                  "Could not import any enricher. "
                  "Please install either requirements.txt (full) or requirements-lite.txt (lite)"
              )


def create_batch_enricher(batch_size: int = 32, force_lite: Optional[bool] = None):
  """
  Create the appropriate BatchEnricher based on environment.
  
  Args:
      batch_size: Number of tweets to batch before processing
      force_lite: If True, force lite version. If False, force full version.
                  If None, auto-detect based on environment.
  
  Returns:
    BatchEnricher instance (either lite or full version)
  """
  enricher = create_enricher(force_lite=force_lite)
  
  # Import the appropriate BatchEnricher
  if "enrichment_lite" in enricher.__module__:
    from .enrichment_lite import BatchEnricher
  else:
    from .enrichment import BatchEnricher
  
  return BatchEnricher(batch_size=batch_size, enricher=enricher)


def get_enricher_info() -> dict:
  """
  Get information about which enricher will be used.
  
  Returns:
    Dictionary with enricher information
  """
  use_lite_env = os.getenv("USE_LITE_ENRICHMENT", "").lower()
  environment = os.getenv("ENVIRONMENT", "development").lower()
  
  # Determine which version will be used
  if use_lite_env in ("1", "true", "yes"):
    version = "lite"
    reason = "USE_LITE_ENRICHMENT=1"
  elif use_lite_env in ("0", "false", "no"):
    version = "full"
    reason = "USE_LITE_ENRICHMENT=0"
  elif environment in ("development", "dev", "local"):
    version = "lite"
    reason = f"ENVIRONMENT={environment}"
  elif environment in ("production", "prod", "staging"):
    version = "full"
    reason = f"ENVIRONMENT={environment}"
  else:
    version = "lite"
    reason = "default"
  
  return {
    "version": version,
    "reason": reason,
    "environment": environment,
    "use_lite_env": use_lite_env or "not set",
    "model": "VADER" if version == "lite" else "DistilBERT",
    "size": "~1MB" if version == "lite" else "~3GB",
    "accuracy": "80-85%" if version == "lite" else "90-95%",
  }
