from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.shazam import FindMatchesFGP 
from app.db.db_clients import DBClient
from app.models.model import Match
from app.utils.utils import GetLogger
from app.api.songs import get_db_client
router = APIRouter(prefix="/fourio", tags=["matching"])
logger = GetLogger()


class FingerprintData(BaseModel):
    # Dict(address -> sampleTimeMs)
    fingerprint: Dict[int, int] 

# --------------------------------------------------------------------
# POST /fourio/match (handleNewFingerprint)
# --------------------------------------------------------------------
@router.post("/match", response_model=List[Match])
async def handle_new_fingerprint(data: FingerprintData, db: DBClient = Depends(get_db_client)):
    """
    Matches the client-side fingerprint against the database and returns ranked matches.
    """
    # Fingerprint is a map (address -> anchorTimeMs)
    fingerprint_map = data.fingerprint
    
    # The matching function handles DB interaction internally
    matches, _, err = FindMatchesFGP(fingerprint_map)
    
    if err:
        logger.error(f"Failed to get matches: {err}")
        raise HTTPException(500, detail=f"Failed to perform fingerprint matching: {err}")
        
    if len(matches) > 10:
        matches = matches[:10]

    return matches