from pydantic import BaseModel, Field
from typing import NamedTuple   

class Peak:
    Time: float  
    Freq: complex 
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

class MaxPeakInfo(NamedTuple):
    max_mag: float
    max_freq: complex
    freq_idx: int