import os
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional
from pydantic import BaseModel

# # Equivalent of Go's fmt package for errors
# from traceback import format_exc
from models import Couple
from utils import GetEnv
class Song(BaseModel):
    """Represents a registered song in the database."""
    Title: str
    Artist: str
    YouTubeID: str

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





DBtype = GetEnv("DB_TYPE", "sqlite")

# NOTE: In Python, the concrete client implementations (MongoClient, SQLiteClient) 
# would typically be in separate files (mongo_client.py, sqlite_client.py), 
# but for a direct file-to-file translation, we'll put the factory here.

# Forward declarations for type hinting the return values
# In a real Python app, you'd import these from their respective files.
class MongoClient(DBClient): ...
class SQLiteClient(DBClient): ...
def NewMongoClient(uri: str) -> Tuple[Optional[MongoClient], Optional[Exception]]: ...
def NewSQLiteClient(dataSourceName: str) -> Tuple[Optional[SQLiteClient], Optional[Exception]]: ...

def NewDBClient() -> Tuple[Optional[DBClient], Optional[Exception]]:
    
    if DBtype == "mongo":
        dbUsername = GetEnv("DB_USER")
        dbPassword = GetEnv("DB_PASS")
        dbName     = GetEnv("DB_NAME")
        dbHost     = GetEnv("DB_HOST")
        dbPort     = GetEnv("DB_PORT")

        if dbUsername and dbPassword:
            dbUri = f"mongodb://{dbUsername}:{dbPassword}@{dbHost}:{dbPort}/{dbName}"
        else:
            dbUri = "mongodb://localhost:27017" # default 

        return NewMongoClient(dbUri)
            
    elif DBtype == "sqlite":
        return NewSQLiteClient("db/db.sqlite3")

    else:
        return None, Exception(f"unsupported database type: {DBtype}")