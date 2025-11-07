import os
import random
from typing import Optional

def GenerateUniqueID() -> int:
    return random.getrandbits(32)

def GenerateSongKey(songTitle: str, songArtist: str) -> str:
    return f"{songTitle}---{songArtist}"

def GetEnv(key: str, fallback: Optional[str] = None) -> str:
    value = os.getenv(key)
    if value is not None:
        return value
    
    if fallback is not None:
        return fallback
        
    return ""
