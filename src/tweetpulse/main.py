from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

from tweetpulse.core.config import get_settings
from tweetpulse.api.v1 import tweets, health
from tweetpulse.api import elastic

settings = get_settings()

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("tweetpulse")

app = FastAPI(
    title="TweetPulse",
    description="Real-time social intelligence platform",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
  start_time = time.time()
  response = await call_next(request)

  process_time = time.time() - start_time
  logger.info(
      f"{request.method} {request.url.path} - "
      f"Status: {response.status_code} - Time: {process_time:.3f}s"
  )

  response.headers["X-Process-Time"] = str(process_time)
  return response

app.include_router(health.router)
app.include_router(tweets.router, prefix="/api")
app.include_router(elastic.router)


@app.on_event("startup")
async def startup_event():
  logger.info("Starting TweetPulse API...")

  if not settings.TWITTER_BEARER_TOKEN:
    logger.warning("TWITTER_BEARER_TOKEN not configured")

  logger.info("TweetPulse API ready")


@app.on_event("shutdown")
async def shutdown_event():
  logger.info("Shutting down TweetPulse API...")

if __name__ == "__main__":
  import uvicorn
  uvicorn.run(
      app,
      host=settings.HOST,
      port=settings.PORT,
      reload=settings.DEBUG,
      log_level="info" if not settings.DEBUG else "debug"
  )
