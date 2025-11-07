from .fingerprints import router as fingerprints_router
from .songs import router as songs_router
from .recordings import router as recordings_router

routers = [fingerprints_router, songs_router, recordings_router]
