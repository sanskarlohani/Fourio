from pydantic import BaseModel, Field
from typing import NamedTuple   
from dataclasses import dataclass

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

class Peak:
    Time: float  
    Freq: complex 
    
class Song(BaseModel):
    """Represents a registered song in the database."""
    Title: str
    Artist: str
    YouTubeID: str
    
class Match(BaseModel):
    """Represents a match found by the Shazam algorithm."""
    SongID: int = Field(..., ge=0)
    SongTitle: str
    SongArtist: str
    YouTubeID: str
    Timestamp: int = Field(..., ge=0)
    Score: float = Field(..., ge=0)
    
class Couple(BaseModel):
    """Represents a time-frequency pair fingerprint."""
    AnchorTimeMs: int = Field(..., ge=0)
    SongID: int = Field(..., ge=0)

class RecordData(BaseModel):
    """Represents data for an audio recording."""
    Audio: str
    Duration: float
    Channels: int
    SampleRate: int
    SampleSize: int

class MaxPeakInfo(NamedTuple):
    max_mag: float
    max_freq: complex
    freq_idx: int

@dataclass
class Track:
    Title: str
    Artist: str
    Album: str
    Artists: list[str]
    Duration: int

class DBClient(ABC):
    @abstractmethod
    def Close(self) -> Optional[Exception]:
        pass

    @abstractmethod
    def StoreFingerprints(self, fingerprints: Dict[int, Couple]) -> Optional[Exception]:
        pass

    @abstractmethod
    def GetCouples(self, addresses: List[int]) -> Tuple[Dict[int, List[Couple]], Optional[Exception]]:
        pass

    @abstractmethod
    def TotalSongs(self) -> Tuple[int, Optional[Exception]]:
        pass

    @abstractmethod
    def RegisterSong(self, songTitle: str, songArtist: str, ytID: str) -> Tuple[int, Optional[Exception]]:
        pass

    @abstractmethod
    def GetSong(self, filterKey: str, value: Any) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        pass

    @abstractmethod
    def GetSongByID(self, songID: int) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        pass

    @abstractmethod
    def GetSongByYTID(self, ytID: str) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        pass

    @abstractmethod
    def GetSongByKey(self, key: str) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        pass

    @abstractmethod
    def DeleteSongByID(self, songID: int) -> Optional[Exception]:
        pass

    @abstractmethod
    def DeleteCollection(self, collectionName: str) -> Optional[Exception]:
        pass