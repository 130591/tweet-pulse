from fastapi import FastAPI

app = FastAPI(title="TweetPulse", description="Real-time social intelligence platform")

@app.get("/")
async def root():
    return {"message": "TweetPulse API is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
