import json
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.db.db_clients import NewDBClient
from app.models.model import DBClient
from app.services.spotify.spotify_service import TrackInfo, PlaylistInfo, AlbumInfo 
from app.utils.utils import GenerateSongKey
from app.utils.logger_setup import GetLogger
from app.services.spotify.download_manager import DlAlbum, DlPlaylist, DlSingleTrack

router = APIRouter(prefix="/songs", tags=["songs"])
logger = GetLogger()
SONGS_DIR = "songs" 

def get_db_client() -> DBClient:
    db_client, err = NewDBClient()
    if err:
        logger.error(f"Error connecting to DB: {err}")
        raise HTTPException(status_code=500, detail="Database connection error")
    return db_client

def download_status(status_type: str, message: str) -> str:
    data = {"type": status_type, "message": message}
    return json.dumps(data)

# --------------------------------------------------------------------
# 1. GET /songs/total (handleTotalSongs)
# --------------------------------------------------------------------
@router.get("/total", response_model=Dict[str, int])
def handle_total_songs(db: DBClient = Depends(get_db_client)):
    """Returns the total number of indexed songs in the database."""
    try:
        total_songs, err = db.TotalSongs()
        if err:
            logger.error(f"Error getting total songs: {err}")
            raise HTTPException(status_code=500, detail="Failed to retrieve song count")
            
        return {"totalSongs": total_songs}
    finally:
        pass

# --------------------------------------------------------------------
# 2. POST /songs/download (handleSongDownload)
# --------------------------------------------------------------------
@router.post("/download", response_model=Dict[str, Any])
async def handle_song_download(spotify_url: str, db: DBClient = Depends(get_db_client)):
    """
    Initiates concurrent download and processing for Spotify links (Album, Playlist, Track).
    """
    # --- Helper to manage background task results ---
    def _handle_download_result(dl_func, url, type_name):
        total_downloaded, err = dl_func(url, SONGS_DIR)
        
        if err:
            logger.error(f"Failed to download {type_name} {url}: {err}")
            short_err = str(err)[:50] if len(str(err)) > 50 else str(err)
            return download_status("error", f"Couldn't download {type_name}. Error: {short_err}")

        status_msg = f"{total_downloaded} songs downloaded from {type_name}."
        return download_status("success", status_msg)
    
    if "album" in spotify_url:
        tracks_in_album, err = AlbumInfo(spotify_url)
        if err: raise HTTPException(500, detail=f"Error getting album info: {str(err)[:50]}")
        logger.info(f"{len(tracks_in_album)} songs found in album.")
        
        status_json = _handle_download_result(DlAlbum, spotify_url, "album")
        return {"status": status_json}

    elif "playlist" in spotify_url:
        tracks_in_pl, err = PlaylistInfo(spotify_url)
        if err: raise HTTPException(500, detail=f"Error getting playlist info: {str(err)[:50]}")
        logger.info(f"{len(tracks_in_pl)} songs found in playlist.")
        
        status_json = _handle_download_result(DlPlaylist, spotify_url, "playlist")
        return {"status": status_json}

    elif "track" in spotify_url:
        track_info, err = TrackInfo(spotify_url)
        if err: raise HTTPException(500, detail=f"Error getting track info: {str(err)[:50]}")
        
        song_key = GenerateSongKey(track_info.Title, track_info.Artist)
        _, song_exists, err = db.GetSongByKey(song_key)
        
        if song_exists:
            song, _, _ = db.GetSongByKey(song_key) 
            msg = f"'{song.Title}' by '{song.Artist}' already exists in the database (https://www.youtube.com/watch?v={song.YouTubeID})"
            return {"status": download_status("error", msg)}
        
        total_downloads, err = DlSingleTrack(spotify_url, SONGS_DIR)

        if err:
            return {"status": download_status("error", str(err))}
        
        if total_downloads == 1:
            msg = f"'{track_info.Title}' by '{track_info.Artist}' was downloaded"
            return {"status": download_status("success", msg)}
        else:
            msg = f"'{track_info.Title}' by '{track_info.Artist}' failed to download"
            return {"status": download_status("error", msg)}

    raise HTTPException(status_code=400, detail="Invalid Spotify URL format.")