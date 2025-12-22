from typing import Dict, List, Tuple, Any, Optional

from pymongo import MongoClient as PyMongoClient
from pymongo import ASCENDING, errors as mongo_errors


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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.Close()

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
      fingerprint_collection = self._db["fingerprints"]
      
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
      fingerprint_collection = self._db["fingerprints"]
      couples_map: Dict[int, List[Couple]] = {}

      try:
          cursor = fingerprint_collection.find({"_id": {"$in": addresses}})
          
          for doc in cursor:
              address = doc.get("_id")
              couples_list = doc.get("couples", [])
              
              doc_couples: List[Couple] = []
              for item in couples_list:
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
        try:
            total = self._db["songs"].count_documents({})
            return total, None
        except Exception as e:
            return 0, e

    def RegisterSong(self, songTitle: str, songArtist: str, ytID: str) -> Tuple[int, Optional[Exception]]:
        songs_collection = self._db["songs"]

        try:
            songs_collection.create_index(
                [("ytID", ASCENDING), ("key", ASCENDING)],
                unique=True
            )
        except Exception as e:
            pass

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