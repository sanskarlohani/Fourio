from typing import Dict, List, Tuple, Any, Optional

from pymongo import MongoClient as PyMongoClient
from pymongo import ASCENDING, errors as mongo_errors, UpdateOne


from app.models.model import Couple, Song, DBClient
from app.utils.utils import GenerateUniqueID, GenerateSongKey

# --- Constants ---
DATABASE_NAME = "song-recognition"
MONGODB_FILTER_KEYS = {"_id", "ytID", "key"}

    
# --- client class ---
class MongoClient(DBClient):
    def __init__(self, client: PyMongoClient):
      self._client = client
      self._db = self._client[DATABASE_NAME]
      self._ensure_indexes()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.Close()

    def _ensure_indexes(self):
        """Ensure all required indexes exist."""
        try:
            # index for songs collection
            self._db["songs"].create_index(
                [("ytID", ASCENDING), ("key", ASCENDING)],
                unique=True,
                background=True
            )
            
            # The fingerprints._id index already exists by default
            # But we verify it's there
            indexes = self._db["fingerprints"].list_indexes()
            has_id_index = any(idx.get("key", {}).get("_id") for idx in indexes)
            if not has_id_index:
                print("[WARNING] _id index missing on fingerprints collection")
                
        except Exception as e:
            print(f"[WARNING] Error ensuring indexes: {e}")
    @staticmethod
    def _map_song_key(key: str) -> Tuple[str, str]:
      """split 'title---artist' key back to title and artist."""
      parts = key.split("---", 1)
      return parts if len(parts) == 2 else ("", "")

    def Close(self) -> Optional[Exception]:
      if self._client:
          self._client.close()
      return None

    def StoreFingerprints(self, fingerprints: Dict[int, Couple]) -> Optional[Exception]:
        """
        stores fingerprints using bulk_write to prevent timeouts  
        errors caused by thousands of individual update_one calls.
        """
        if not fingerprints:
            return None
        fingerprint_collection = self._db["fingerprints"]
        updates = []
        batch_size = 5000
        import time
        print(f"[DB DEBUG] Preparing bulk update for {len(fingerprints)} fingerprints...")
        start_time = time.perf_counter()
        try:
            for address, couple in fingerprints.items():
                # define the operation for this specific fingerprint
                op = UpdateOne(
                    {"_id": address},
                    {
                        "$push": {
                            "couples": {
                                "AnchorTimeMs": couple.AnchorTimeMs,
                                "SongID": couple.SongID,
                            }
                        }
                    },
                    upsert=True
                )
                updates.append(op)

                # when the batch is full, send it to the database
                if len(updates) >= batch_size:
                    fingerprint_collection.bulk_write(updates, ordered=False)
                    updates = [] # clear the batch
            if updates:
                fingerprint_collection.bulk_write(updates, ordered=False)

            end_time = time.perf_counter()
            print(f"Time taken for storing fingerprints: {end_time - start_time:.2f} seconds")
            return None
        except Exception as e:
            return Exception(f"error upserting document: {e}")

    def GetCouples(self, addresses: List[int]) -> Tuple[Dict[int, List[Couple]], Optional[Exception]]:
        """
        Optimized version with batching and list comprehension.
        """
        fingerprint_collection = self._db["fingerprints"]

        if not addresses:
            return {}, None
        
        couples_map: Dict[int, List[Couple]] = {}
        BATCH_SIZE = 1000

        try:
            # Process addresses in batches
            for i in range(0, len(addresses), BATCH_SIZE):
                batch = addresses[i:i + BATCH_SIZE]
                
                # Use aggregation pipeline for better performance
                pipeline = [
                    {"$match": {"_id": {"$in": batch}}},
                    {"$project": {"_id": 1, "couples": 1}}
                ]
            cursor = fingerprint_collection.aggregate(pipeline, allowDiskUse=True)
          
            for doc in cursor:
                address = doc.get("_id")
                couples_list = doc.get("couples", [])
                
                doc_couples = [
                    Couple(
                        AnchorTimeMs=item.get("AnchorTimeMs", 0),
                        SongID=item.get("SongID", 0)
                    )
                    for item in couples_list
                    if isinstance(item, dict)
                ] 
              
                if address is not None:
                    couples_map[address] = doc_couples
          
            return couples_map, None
        except Exception as e:
            return {}, Exception(f"error retrieving documents: {e}")


    def TotalSongs(self) -> Tuple[int, Optional[Exception]]:
        try:
            total = self._db["songs"].count_documents({})
            return total, None
        except Exception as e:
            return 0, e

    def RegisterSong(self, songTitle: str, songArtist: str, ytID: str) -> Tuple[int, Optional[Exception]]:
        songs_collection = self._db["songs"]

        try:
            songID = GenerateUniqueID()
            key = GenerateSongKey(songTitle, songArtist)
            
            result = songs_collection.insert_one({
                "_id": songID, 
                "key": key, 
                "ytID": ytID,
                "Title": songTitle, 
                "Artist": songArtist, 
            })
            return songID, None
            
        except mongo_errors.DuplicateKeyError as e:
            return 0, Exception(f"song with ytID or key already exists: {e}")
        except Exception as e:
            return 0, Exception(f"failed to register song: {e}")

    def GetSong(self, filterKey: str, value: Any) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        if filterKey not in MONGODB_FILTER_KEYS:
            return None, False, Exception("invalid filter key")

        songs_collection = self._db["songs"]
        
        filter_value = value
        
        try:
            song_doc = songs_collection.find_one({filterKey: filter_value})
            
            if not song_doc:
                return None, False, None 

            ytID = song_doc.get("ytID", "")
            key = song_doc.get("key", "")
            title, artist = self._map_song_key(key) 

            song_instance = Song(
                Title=title, 
                Artist=artist, 
                YouTubeID=ytID
            )
            return song_instance, True, None
            
        except Exception as e:
            return None, False, Exception(f"failed to retrieve song: {e}")


    def GetSongByID(self, songID: int) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        return self.GetSong("_id", songID)
    
    def GetSongsByIDs(self, songIDs: List[int]) -> Tuple[Dict[int, Song], Optional[Exception]]:
        """Fetch multiple songs in a single MongoDB query."""
        if not songIDs:
            return {}, None
        
        songs_collection = self._db["songs"]
        
        try:
            cursor = songs_collection.find(
                {"_id": {"$in": songIDs}},
                {"_id": 1, "key": 1, "ytID": 1}
            )
            
            songs_map = {}
            for doc in cursor:
                songID = doc.get("_id")
                ytID = doc.get("ytID", "")
                key = doc.get("key", "")
                title, artist = self._map_song_key(key)
                
                song = Song(
                    Title=title,
                    Artist=artist,
                    YouTubeID=ytID
                )
                songs_map[songID] = song
            
            return songs_map, None
        except Exception as e:
            return {}, Exception(f"failed to retrieve songs: {e}")

    def GetSongByYTID(self, ytID: str) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        return self.GetSong("ytID", ytID)

    def GetSongByKey(self, key: str) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        return self.GetSong("key", key)

    def DeleteSongByID(self, songID: int) -> Optional[Exception]:
        try:
            self._db["songs"].delete_one({"_id": songID})
            return None
        except Exception as e:
            return Exception(f"failed to delete song: {e}")

    def DeleteCollection(self, collectionName: str) -> Optional[Exception]:
        try:
            self._db.drop_collection(collectionName)
            return None
        except Exception as e:
            return Exception(f"error deleting collection: {e}")
        
# --- factory method ---
def NewMongoClient(uri: str) -> Tuple[Optional[MongoClient], Optional[Exception]]:
    try:
        client = PyMongoClient(uri)
        client.admin.command('ping')
        return MongoClient(client), None
    except Exception as e:
        return None, Exception(f"error connecting to MongoDB: {e}")