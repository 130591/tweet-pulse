import os
from typing import Optional
from pathlib import Path
from datetime import datetime

class Settings:
	# API Keys
	TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN", "")
	
	# Database
	DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/tweetpulse")
	REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
	DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "False").lower() == "true"
	
	# App
	DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
	HOST: str = os.getenv("HOST", "0.0.0.0")
	PORT: int = int(os.getenv("PORT", "8000"))
	
	# Rate Limits
	MAX_TWEETS_PER_REQUEST: int = 100
	REQUEST_TIMEOUT: int = 30
	
	# Feature Flags
	ENABLE_DEBUGPY: bool = os.getenv("ENABLE_DEBUGPY", "False").lower() == "true"

	# Pipeline
	NUM_WORKERS: int = 3
	STAGING_DIR: Path = Path("./staging")
	BATCH_WRITE_INTERVAL: int = 300
	
	# Logging
	LOG_LEVEL: str = "INFO"

settings = Settings()

def get_settings() -> Settings:
	return settings
