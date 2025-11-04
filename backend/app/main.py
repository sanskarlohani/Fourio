from fastapi import FastAPI
from app.utils.utils import GetLogger

from app.api import songs, recordings, fingerprints

app = FastAPI(
  title="Fourio Backend",
  description="Backend service for audio fingerprinting and Spotify integration.",
  version="1.0.0"
)
logger = GetLogger()

app.include_router(songs.router)
app.include_router(recordings.router)
app.include_router(fingerprints.router)


@app.get("/", include_in_schema=False)
def read_root():
    return {"message": "Backend is running. See /docs for API endpoints."}


if __name__ == "__main__":
    # run: uvicorn app.main:app --reload
    import uvicorn
    logger.info("starting server...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)