from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import time

from .core.config import settings
from .core.dependencies import get_tweet_fetcher

logging.basicConfig(
	level=logging.INFO if not settings.DEBUG else logging.DEBUG,
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("tweetpulse")

app = FastAPI(
	title="TweetPulse",
	description="Real-time social intelligence platform",
	version="1.0.0",
	debug=settings.DEBUG
)

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["GET", "POST", "PUT", "DELETE"],
	allow_headers=["*"],
)

app.add_middleware(
	TrustedHostMiddleware,
	allowed_hosts=["localhost", "127.0.0.1"],
)


@app.middleware("http")
async def log_requests(request, call_next):
	start_time = time.time()
	
	response = await call_next(request)
	
	process_time = time.time() - start_time
	logger.info(
		f"{request.method} {request.url.path} - "
		f"Status: {response.status_code} - Time: {process_time:.3f}s"
	)
	
	response.headers["X-Process-Time"] = str(process_time)
	return response

@app.get("/")
async def root():
  return {"message": "TweetPulse API is running!", "version": "1.0.0"}

@app.get("/health")
async def health():
  return {"status": "healthy", "debug": settings.DEBUG}

@app.get("/tweets")
async def get_tweets(
  fetcher = Depends(get_tweet_fetcher)
):
  return await fetcher.fetch_tweets("python", settings.MAX_TWEETS_PER_REQUEST)

@app.get("/settings")
async def get_app_settings():
	return {
		"debug": settings.DEBUG,
		"max_tweets_per_request": settings.MAX_TWEETS_PER_REQUEST,
		"twitter_configured": bool(settings.TWITTER_BEARER_TOKEN)
	}

@app.on_event("startup")
async def startup_event():
	logger.info("🚀 TweetPulse API iniciando...")
	if not settings.TWITTER_BEARER_TOKEN:
		logger.warning("⚠️  TWITTER_BEARER_TOKEN não configurado!")
	else:
		logger.info("✅ Twitter API configurada")

@app.on_event("shutdown")
async def shutdown_event():
  logger.info("👋 TweetPulse API finalizando...")

if __name__ == "__main__":
	import uvicorn
	
	uvicorn.run(
		"main:app",
		host=settings.HOST,
		port=settings.PORT,
		reload=settings.DEBUG,
		log_level="info" if not settings.DEBUG else "debug"
	)