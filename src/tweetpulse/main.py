from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi import Request
import os
import logging

# Optional: enable debugpy inside container for VS Code attach
if os.getenv("ENABLE_DEBUGPY") == "1":
    try:
        import debugpy  # type: ignore
        _dbg_port = int(os.getenv("DEBUGPY_PORT", "5678"))
        debugpy.listen(("0.0.0.0", _dbg_port))
        if os.getenv("DEBUGPY_WAIT_FOR_CLIENT") == "1":
            print(f"Waiting for debugger attach on 0.0.0.0:{_dbg_port} ...")
            debugpy.wait_for_client()
    except Exception as _e:  # pragma: no cover
        print(f"debugpy setup failed: {_e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tweetpulse")

ALLOWED_ORIGINS = [item.strip() for item in (os.getenv("ALLOWED_ORIGINS") or "*").split(",")]
ALLOWED_HOSTS = [item.strip() for item in (os.getenv("ALLOWED_HOSTS") or "localhost,127.0.0.1").split(",")]

app = FastAPI(title="TweetPulse", description="Real-time social intelligence platform")

app.add_middleware(
	CORSMiddleware,
	allow_origins=ALLOWED_ORIGINS or ["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)
	
app.add_middleware(
	TrustedHostMiddleware,
	allowed_hosts=ALLOWED_HOSTS or ["localhost", "127.0.0.1"],
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
	import uuid
	request_id = str(uuid.uuid4())
	request.state.request_id = request_id
	
	response = await call_next(request)
	response.headers["X-Request-ID"] = request_id
	
	return response
    
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
	import time
	start_time = time.time()
	
	response = await call_next(request)
	
	process_time = time.time() - start_time
	response.headers["X-Process-Time"] = str(process_time)
	
	logger.info(
		f"{request.method} {request.url.path} - "
		f"Status: {response.status_code} - Time: {process_time:.3f}s"
	)
	
	return response
	

@app.get("/")
async def root():
  return {"message": "TweetPulse API is running!"}

@app.get("/health")
async def health():
  return {"status": "healthy"}

if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=8000)
