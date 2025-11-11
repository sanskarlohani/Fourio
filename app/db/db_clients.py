from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional

from app.models.model import Couple, Song
from app.utils.utils import GetEnv
from .mongo_client import NewMongoClient
from .sqlite_client import NewSQLiteClient

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