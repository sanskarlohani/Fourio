from pydantic import BaseModel, Field
from typing import Dict, List

class Song(BaseModel):
    """Represents a registered song in the database."""
    Title: str
    Artist: str
    YouTubeID: str
    
class Couple(BaseModel):
    """Represents a time-frequency pair fingerprint."""
    AnchorTimeMs: int = Field(..., ge=0)
    SongID: int = Field(..., ge=0)

class RecordData(BaseModel):
    """Represents data for an audio recording."""
    audio: str
    duration: float
    channels: int
    SampleRate: int
    SampleSize: int