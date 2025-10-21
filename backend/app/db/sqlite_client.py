import sqlite3
from typing import Dict, List, Tuple, Any, Optional

from db_clients import DBClient, Song
from models.model import Couple
from utils.utils import GenerateUniqueID, GenerateSongKey

SQLITE_FILTER_KEYS = {"id", "ytID", "key"}
SQLITE_CONSTRAINT_ERROR = 'UNIQUE constraint failed' # Common message for constraint error


def _create_tables(db_conn: sqlite3.Connection) -> Optional[Exception]:
    try:
        cursor = db_conn.cursor()
        create_songs_table = """
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                ytID TEXT,
                key TEXT NOT NULL UNIQUE
            );
        """
        create_fingerprints_table = """
            CREATE TABLE IF NOT EXISTS fingerprints (
                address INTEGER NOT NULL,
                anchorTimeMs INTEGER NOT NULL,
                songID INTEGER NOT NULL,
                PRIMARY KEY (address, anchorTimeMs, songID)
            );
        """
        cursor.execute(create_songs_table)
        cursor.execute(create_fingerprints_table)
        db_conn.commit()
        return None
    except sqlite3.Error as e:
        return Exception(f"error creating tables: {e}")

class SQLiteClient(DBClient):    
    def __init__(self, db_conn: sqlite3.Connection):
        self._db = db_conn

    def Close(self) -> Optional[Exception]:
        if self._db:
            self._db.close()
        return None

    def StoreFingerprints(self, fingerprints: Dict[int, Couple]) -> Optional[Exception]:
        try:
            with self._db: 
                cursor = self._db.cursor()
                sql = "INSERT OR REPLACE INTO fingerprints (address, anchorTimeMs, songID) VALUES (?, ?, ?)"
                data = [(a, c.AnchorTimeMs, c.SongID) for a, c in fingerprints.items()]
                cursor.executemany(sql, data)
            return None
        except sqlite3.Error as e:
            return Exception(f"error storing fingerprints: {e}")


    def GetCouples(self, addresses: List[int]) -> Tuple[Dict[int, List[Couple]], Optional[Exception]]:
        couples_map: Dict[int, List[Couple]] = {}

        try:
            cursor = self._db.cursor()
            placeholders = ','.join(['?'] * len(addresses))
            sql = f"SELECT address, anchorTimeMs, songID FROM fingerprints WHERE address IN ({placeholders})"
            cursor.execute(sql, addresses)
            
            for row in cursor.fetchall():
                address, anchor_time_ms, song_id = row
                couple = Couple(AnchorTimeMs=anchor_time_ms, SongID=song_id)
                couples_map.setdefault(address, []).append(couple)

            return couples_map, None
        except sqlite3.Error as e:
            return {}, Exception(f"error querying database: {e}")

    def TotalSongs(self) -> Tuple[int, Optional[Exception]]:
        try:
            cursor = self._db.cursor()
            count = cursor.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
            return count, None
        except sqlite3.Error as e:
            return 0, Exception(f"error counting songs: {e}")

    def RegisterSong(self, songTitle: str, songArtist: str, ytID: str) -> Tuple[int, Optional[Exception]]:
        try:
            with self._db:
                cursor = self._db.cursor()
                sql = "INSERT INTO songs (id, title, artist, ytID, key) VALUES (?, ?, ?, ?, ?)"
                
                songID = GenerateUniqueID() 
                songKey = GenerateSongKey(songTitle, songArtist) 
                
                cursor.execute(sql, (songID, songTitle, songArtist, ytID, songKey))
                return songID, None
                
        except sqlite3.IntegrityError as e:
            if SQLITE_CONSTRAINT_ERROR in str(e):
                return 0, Exception(f"song with ytID or key already exists: {e}")
            return 0, Exception(f"failed to register song: {e}")
        except Exception as e:
            return 0, Exception(f"failed to register song: {e}")

    def GetSong(self, filterKey: str, value: Any) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        if filterKey not in SQLITE_FILTER_KEYS:
            return None, False, Exception("invalid filter key")

        try:
            cursor = self._db.cursor()
            query = f"SELECT title, artist, ytID FROM songs WHERE {filterKey} = ?"
            
            row = cursor.execute(query, (value,)).fetchone()
            
            if not row:
              return None, False, None 

            title, artist, ytID = row
            song_instance = Song(Title=title, Artist=artist, YouTubeID=ytID)
            return song_instance, True, None
            
        except sqlite3.Error as e:
            return None, False, Exception(f"failed to retrieve song: {e}")
        
    def GetSongByID(self, songID: int) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        return self.GetSong("id", songID)

    def GetSongByYTID(self, ytID: str) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        return self.GetSong("ytID", ytID)

    def GetSongByKey(self, key: str) -> Tuple[Optional[Song], bool, Optional[Exception]]:
        return self.GetSong("key", key)

    def DeleteSongByID(self, songID: int) -> Optional[Exception]:
        try:
            with self._db:
              self._db.execute("DELETE FROM songs WHERE id = ?", (songID,))
            return None
        except Exception as e:
            return Exception(f"failed to delete song: {e}")

    def DeleteCollection(self, collectionName: str) -> Optional[Exception]:
        try:
            with self._db:
              self._db.execute(f"DROP TABLE IF EXISTS {collectionName}")
            return None
        except Exception as e:
            return Exception(f"error deleting collection: {e}")

# --- factory method ---
def NewSQLiteClient(dataSourceName: str) -> Tuple[Optional[SQLiteClient], Optional[Exception]]:
    
    # busy timeout parameter to DSN (milliseconds)
    if '?' in dataSourceName:
        if '_busy_timeout' not in dataSourceName:
            dataSourceName += "&_busy_timeout=5000"
    else:
        dataSourceName += "?_busy_timeout=5000"

    try:
        db_conn = sqlite3.connect(dataSourceName)
        
        err = _create_tables(db_conn)
        if err:
            db_conn.close()
            return None, Exception(f"error creating tables: {err}")

        return SQLiteClient(db_conn), None
    except sqlite3.Error as e:
        return None, Exception(f"error connecting to SQLite: {e}")
    except Exception as e:
        return None, Exception(f"error creating tables: {e}")
