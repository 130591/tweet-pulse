from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import time

from .api.v1 import tweets
from .core.config import settings

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

app.include_router(tweets.router, prefix="/health", tags=["health"])
app.include_router(tweets.router, prefix="/tweets", tags=["tweets"])
app.include_router(tweets.router, prefix="/settings", tags=["settings"])
app.include_router(tweets.router, prefix="/stats", tags=["stats"])

@app.on_event("startup")
async def startup_event():
	logger.info("🚀 TweetPulse API starting...")
	if not settings.TWITTER_BEARER_TOKEN:
		logger.warning("⚠️  TWITTER_BEARER_TOKEN not configured!")
	else:
		logger.info("✅ Twitter API configured")

@app.on_event("shutdown")
async def shutdown_event():
  logger.info("👋 TweetPulse API shutting down...")

if __name__ == "__main__":
	import uvicorn
	
	uvicorn.run(
		"main:app",
		host=settings.HOST,
		port=settings.PORT,
		reload=settings.DEBUG,
		log_level="info" if not settings.DEBUG else "debug"
	)