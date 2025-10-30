import urllib.parse
import os
import subprocess
import platform
import pathlib
from typing import Tuple, Optional
from db.db_clients import NewDBClient


def EncodeParam(s: str) -> str:
    """
    URL-escapes a string 
    """
    return urllib.parse.quote(s)

def ToLowerCase(s: str) -> str:
    return s.lower()

# --- File System Utilities ---

def GetFileSize(file_path: str) -> Tuple[Optional[int], Optional[Exception]]:
    """
    Returns the size of a file in bytes.
    """
    try:
        # os.stat provides file status information, including size
        file_info = os.stat(file_path)
        size = file_info.st_size
        return size, None
    except Exception as e:
        return None, e

def correctFilename(title: str, artist: str) -> Tuple[str, str]:
    """
    Fixes characters invalid in file paths.
    """
    current_os = platform.system()
    
    # Invalid characters for Windows file paths
    invalid_chars = ['<', '>', ':', '"', '\\', '/', '|', '?', '*']
    
    if current_os == "Windows":
        for invalid_char in invalid_chars:
            title = title.replace(invalid_char, "")
            artist = artist.replace(invalid_char, "")
    else:
        title = title.replace("/", "\\")
        artist = artist.replace("/", "\\")

    return title, artist

# --- Database Check Utilities ---

def SongKeyExists(key: str) -> Tuple[bool, Optional[Exception]]:
    """
    Checks if a song key exists in the database.
    """
    db_client, err = NewDBClient()
    if err:
        return False, err
    
    with db_client: 
        _, song_exists, err = db_client.GetSongByKey(key)
        if err:
            return False, err
        return song_exists, None

def YtIDExists(ytID: str) -> Tuple[bool, Optional[Exception]]:
    """
    Checks if a YouTube ID exists in the database.
    """
    db_client, err = NewDBClient()
    if err:
        return False, err
    
    with db_client: 
        _, song_exists, err = db_client.GetSongByYTID(ytID)
        if err:
            return False, err
        return song_exists, None

# --- Audio Processing Utility ---

def convertStereoToMono(stereo_file_path: str) -> Tuple[Optional[bytes], Optional[Exception]]:
    """
    Converts a file to mono and returns audio bytes.
    """
    
    # 1. Prepare Paths
    path_obj = pathlib.Path(stereo_file_path)
    mono_file_path = path_obj.parent / f"{path_obj.stem}_mono{path_obj.suffix}"
    
    try:
        # 2. Check the number of channels using ffprobe
        # The Go logic is explicitly translated here to check if conversion is needed
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "stream=channels", 
            "-of", "default=noprint_wrappers=1:nokey=1", stereo_file_path
        ]
        
        output = subprocess.run(cmd, check=True, capture_output=True, text=True)
        channels = output.stdout.strip()
        
        audio_bytes = path_obj.read_bytes() # Read the original file bytes
        
        if channels != "1":
            # 3. Convert stereo to mono using ffmpeg pan filter
            # Go: cmd = exec.Command("ffmpeg", "-i", stereoFilePath, "-af", "pan=mono|c0=c0", monoFilePath)
            cmd = [
                "ffmpeg", "-i", stereo_file_path, "-af", "pan=mono|c0=c0", str(mono_file_path)
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                raise Exception(f"Error converting stereo to mono: {e.stderr.decode()}")
            
            # 4. Read the newly created mono file
            audio_bytes = mono_file_path.read_bytes()
            
        return audio_bytes, None
        
    except FileNotFoundError:
        return None, Exception("FFmpeg or FFprobe command not found.")
    except Exception as e:
        return None, e
    finally:
        # Clean up the temporary mono file
        if os.path.exists(mono_file_path):
            os.remove(mono_file_path)