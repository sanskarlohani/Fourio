from typing import Dict, List, Tuple, Any, Optional

# Equivalent Python Modules
from pymongo import MongoClient as PyMongoClient
from pymongo import ASCENDING, errors as mongo_errors
from bson.objectid import ObjectId
from bson.errors import InvalidId

# The 'song-recognition' project dependencies
from db_client import DBClient, Song
from models.model import Couple
# Assuming 'utils' is a Python module with GenerateUniqueID, GenerateSongKey
from utils.utils import GenerateUniqueID, GenerateSongKey, GetEnv

# --- Constants ---
DATABASE_NAME = "song-recognition"
MONGODB_FILTER_KEYS = {"_id", "ytID", "key"}
# Note: Python's 'contextlib.nullcontext' or simply omitting 'context.Background()' 
# is the equivalent of passing a default context in Go.

# --- Client Implementation ---
class MongoClient(DBClient):
    """Corresponds to the Go MongoClient struct and implementation."""
    
    def __init__(self, uri: str, client: PyMongoClient):
        self._client = client
        self._db = self._client[DATABASE_NAME]
        
    @staticmethod
    def _map_song_key(key: str) -> Tuple[str, str]:
        """Maps Go's 'title---artist' key back to title and artist."""
        parts = key.split("---", 1)
        return parts if len(parts) == 2 else ("", "")

# --- Factory Function ---
def NewMongoClient(uri: str) -> Tuple[Optional[MongoClient], Optional[Exception]]:
    """Corresponds to the Go NewMongoClient function."""
    try:
        # NOTE: Go's context.Background() is omitted here; PyMongo handles the connection setup.
        client = PyMongoClient(uri)
        # Attempt a server check (optional, but good practice)
        client.admin.command('ping')
        return MongoClient(uri, client), None
    except Exception as e:
        return None, Exception(f"error connecting to MongoDB: {e}")

# --- DBClient Interface Implementation ---

    def Close(self) -> Optional[Exception]:
        """Corresponds to the Go Close method."""
        if self._client:
            self._client.close()
        return None

    def StoreFingerprints(self, fingerprints: Dict[int, Couple]) -> Optional[Exception]:
        """Corresponds to the Go StoreFingerprints method (using bulk updates)."""
        fingerprint_collection = self._db["fingerprints"]
        
        # In PyMongo, bulk_write is often preferred for performance.
        # Translating the Go logic with UpdateOne operations:
        try:
            for address, couple in fingerprints.items():
                filter_query = {"_id": address}
                update_query = {
                    "$push": {
                        "couples": {
                            "AnchorTimeMs": couple.AnchorTimeMs,
                            "SongID": couple.SongID,
                        }
                    }
                }
                fingerprint_collection.update_one(
                    filter_query, 
                    update_query, 
                    upsert=True
                )
            return None
        except Exception as e:
            return Exception(f"error upserting document: {e}")

    def GetCouples(self, addresses: List[int]) -> Tuple[Dict[int, List[Couple]], Optional[Exception]]:
        """Corresponds to the Go GetCouples method."""
        fingerprint_collection = self._db["fingerprints"]
        couples_map: Dict[int, List[Couple]] = {}

        try:
            # Query all addresses at once using $in (more efficient than looping)
            cursor = fingerprint_collection.find({"_id": {"$in": addresses}})
            
            for doc in cursor:
                address = doc.get("_id")
                couples_list = doc.get("couples", [])
                
                doc_couples: List[Couple] = []
                for item in couples_list:
                    # PyMongo returns standard dicts, no need for primitive.M/A casting
                    if isinstance(item, dict):
                        doc_couples.append(Couple(
                            AnchorTimeMs=item.get("AnchorTimeMs", 0),
                            SongID=item.get("SongID", 0)
                        ))
                
                if address is not None:
                    couples_map[address] = doc_couples
            
            return couples_map, None
        except Exception as e:
            return {}, Exception(f"error retrieving documents: {e}")


    def TotalSongs(self) -> Tuple[int, Optional[Exception]]:
        """Corresponds to the Go TotalSongs method."""
        try:
            total = self._db["songs"].count_documents({})
            return total, None
        except Exception as e:
            return 0, e

    def RegisterSong(self, songTitle: str, songArtist: str, ytID: str) -> Tuple[int, Optional[Exception]]:
        """Corresponds to the Go RegisterSong method."""
        songs_collection = self._db["songs"]

        try:
            # Ensure unique index exists on (ytID, key)
            songs_collection.create_index(
                [("ytID", ASCENDING), ("key", ASCENDING)],
                unique=True
            )
        except Exception as e:
            # Index creation should not fail registration unless an actual conflict exists
            pass

        try:
            songID = utils.GenerateUniqueID() # Assumed Python equivalent
            key = utils.GenerateSongKey(songTitle, songArtist) # Assumed Python equivalent
            
            result = songs_collection.insert_one({
                "_id": songID, 
                "key": key, 
                "ytID": ytID,
                "Title": songTitle, # Added to support GetSong logic without splitting key
                "Artist": songArtist, # Added to support GetSong logic without splitting key
            })
            return songID, None
            
        except mongo_errors.DuplicateKeyError as e:
            # Matches Go's handling of duplicate key error
            return 0, Exception(f"song with ytID or key already exists: {e}")
        except Exception as e:
            return 0, Exception(f"failed to register song: {e}")

    def GetSong(self, filterKey: str, value: Any) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        """Corresponds to the Go GetSong method."""
        if filterKey not in MONGODB_FILTER_KEYS:
            return None, False, Exception("invalid filter key")

        songs_collection = self._db["songs"]
        
        # Handle the type casting for _id (if songID is passed as int)
        filter_value = value
        
        try:
            song_doc = songs_collection.find_one({filterKey: filter_value})
            
            if not song_doc:
                return None, False, None # mongo.ErrNoDocuments

            # Extract data. We rely on the 'key' being present as in the Go logic
            ytID = song_doc.get("ytID", "")
            key = song_doc.get("key", "")
            title, artist = self._map_song_key(key) # Use helper for robust key splitting

            song_instance = Song(
                Title=title, 
                Artist=artist, 
                YouTubeID=ytID
            )
            return song_instance, True, None
            
        except Exception as e:
            return None, False, Exception(f"failed to retrieve song: {e}")

    # --- Convenience Wrappers (Go's GetSongByID, etc. equivalents) ---

    def GetSongByID(self, songID: int) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        return self.GetSong("_id", songID)

    def GetSongByYTID(self, ytID: str) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        return self.GetSong("ytID", ytID)

    def GetSongByKey(self, key: str) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        return self.GetSong("key", key)

    # --- Delete Methods ---

    def DeleteSongByID(self, songID: int) -> Optional[Exception]:
        """Corresponds to the Go DeleteSongByID method."""
        try:
            self._db["songs"].delete_one({"_id": songID})
            return None
        except Exception as e:
            return Exception(f"failed to delete song: {e}")

    def DeleteCollection(self, collectionName: str) -> Optional[Exception]:
        """Corresponds to the Go DeleteCollection method."""
        try:
            self._db.drop_collection(collectionName)
            return None
        except Exception as e:
            return Exception(f"error deleting collection: {e}")