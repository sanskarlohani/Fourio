from fastapi import APIRouter
from .fingerprints import router as fingerprints_router
from .songs import router as songs_router
from .recordings import router as recordings_router

router = APIRouter()

for r in [fingerprints_router, songs_router, recordings_router]:
    router.include_router(r)