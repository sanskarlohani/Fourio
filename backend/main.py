from fastapi import FastAPI
from app.api.router import api_router

app = FastAPI(
    title="Furio API",
    version="0.1.0",
    description="Audio fingerprinting & song recognition backend"
)

@app.get("/")
async def root():
    return {"status": "Furio backend running"}


app.include_router(api_router, prefix="/api/")
