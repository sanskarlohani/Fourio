import json
import requests
import urllib.parse
import re
from typing import List, Tuple, Optional, NamedTuple
from datetime import datetime, timedelta

from app.utils.utils import GetEnv
from app.models.model import Track


class ResourceEndpoint(NamedTuple):
    Limit: int = 0
    Offset: int = 0
    TotalCount: int = 0
    Requests: int = 0

class Credentials(NamedTuple):
    ClientID: str
    ClientSecret: str

class TokenResponse(NamedTuple):
    AccessToken: str
    TokenType: str
    ExpiresIn: int

class CachedToken(NamedTuple):
    Token: str
    ExpiresAt: datetime

# --- Constants ---
TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

CACHED_TOKEN_PATH = "token.json"

# --- Authentication and Caching ---
def load_credentials() -> Tuple[Optional[Credentials], Optional[Exception]]:
    client_id = GetEnv("SPOTIFY_CLIENT_ID", "")
    client_secret = GetEnv("SPOTIFY_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        return None, Exception("SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET environment variables not set")

    return Credentials(ClientID=client_id, ClientSecret=client_secret), None

def save_token(token: str, expires_in: int) -> Optional[Exception]:
    try:
        # calculate exp time
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        ct = CachedToken(Token=token, ExpiresAt=expires_at)
        
        data = {
            "token": ct.Token,
            "expires_at": ct.ExpiresAt.isoformat(), 
        }
        
        with open(CACHED_TOKEN_PATH, 'w') as f:
            json.dump(data, f, indent=4) 
        return None
    
    except Exception as e:
        return e

def load_cached_token() -> Tuple[Optional[str], Optional[Exception]]:
    try:
        with open(CACHED_TOKEN_PATH, 'r') as f:
            data = json.load(f)
            
        # Parse ISO datetime string back to datetime object
        expires_at = datetime.fromisoformat(data['expires_at'])
        
        if datetime.now() > expires_at:
            return None, Exception("token expired")
            
        return data['token'], None
        
    except FileNotFoundError:
        return None, Exception("token file not found")
    except json.JSONDecodeError as e:
        return None, Exception(f"invalid token JSON: {e}")
    except Exception as e:
        return None, e


def access_token() -> Tuple[Optional[str], Optional[Exception]]:
    # 1. Try using cached token
    token, err = load_cached_token()
    if err is None:
        return token, None

    # 2. request a new token
    creds, err = load_credentials()
    if err:
        return None, err
    
    try:
        resp = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": creds.ClientID,
                "client_secret": creds.ClientSecret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        resp.raise_for_status() # exception for non-200 status codes

        tr_dict = resp.json()

        tr = TokenResponse(
            AccessToken=tr_dict.get('access_token', ''),
            TokenType=tr_dict.get('token_type', ''),
            ExpiresIn=tr_dict.get('expires_in', 0)
        )
        
        if not tr.AccessToken:
             return None, Exception(f"Token response missing access_token: {resp.text}")

        # Save the new token
        if save_err := save_token(tr.AccessToken, tr.ExpiresIn):
            return None, save_err
            
        return tr.AccessToken, None
        
    except requests.exceptions.RequestException as e:
        # Check if response object exists to get body/status code
        if e.response is not None:
             body = e.response.text
             status = e.response.status_code
             return None, Exception(f"Token request failed (status {status}): {body}")
        return None, Exception(f"Token request failed: {e}")


# --- API Request Helpers ---
def _request(endpoint: str) -> Tuple[int, Optional[str], Optional[Exception]]:
    bearer, err = access_token()
    if err:
        return 0, None, Exception(f"failed to get access token: {err}")

    try:
        headers = {"Authorization": f"Bearer {bearer}"}
        resp = requests.get(endpoint, headers=headers)
        body = resp.text
        
        return resp.status_code, body, None
        
    except requests.exceptions.RequestException as e:
        return 0, None, Exception(f"error on getting response: {e}")

def get_id(url_str: str) -> str:
    path = urllib.parse.urlparse(url_str).path
    parts = path.split('/')
    
    # Assuming the ID is always the 5th part (index 4) after splitting by '/'
    if len(parts) >= 5:
        return parts[4]
    return ""

def is_valid_pattern(url_str: str, pattern: str) -> bool:
    return bool(re.match(pattern, url_str))

# --- Track/Playlist/Album Info Functions ---
def TrackInfo(url_str: str) -> Tuple[Optional[Track], Optional[Exception]]:
    re_pattern = re.compile(r'open\.spotify\.com\/(?:intl-.+\/)?track\/([a-zA-Z0-9]{22})(\?si=[a-zA-Z0-9]{16})?')
    matches = re_pattern.search(url_str)
    
    if not matches:
        return None, Exception("invalid track URL")
        
    track_id = matches.group(1)

    # Use the official Spotify API endpoint structure
    endpoint = f"{SPOTIFY_API_BASE}/tracks/{track_id}"
    
    status_code, json_response, err = _request(endpoint)
    if err:
        return None, Exception(f"error getting track info: {err}")
    if status_code != 200:
        return None, Exception(f"non-200 status code: {status_code}. Response: {json_response}")

    try:
        data = json.loads(json_response)
        
        # Extract artists
        all_artists = [a['name'] for a in data.get('artists', [])]
        primary_artist = all_artists[0] if all_artists else ""
        
        track = Track(
            Title=data.get('name', ''),
            Artist=primary_artist,
            Artists=all_artists,
            Album=data.get('album', {}).get('name', ''),
            Duration=data.get('duration_ms', 0) // 1000 # ms to seconds
        )
        return track, None
        
    except json.JSONDecodeError as e:
        return None, Exception(f"failed to parse track JSON: {e}")
    except Exception as e:
        return None, e


def PlaylistInfo(url_str: str) -> Tuple[List[Track], Optional[Exception]]:
    re_pattern = re.compile(r'open\.spotify\.com\/playlist\/([a-zA-Z0-9]{22})')
    matches = re_pattern.search(url_str)
    if not matches:
        return [], Exception("invalid playlist URL")
        
    playlist_id = matches.group(1)

    all_tracks: List[Track] = []
    offset = 0
    limit = 100
    total = 1 

    while offset < total:
        # Use the official Spotify API endpoint structure
        endpoint = f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/tracks?offset={offset}&limit={limit}"
        status_code, json_response, err = _request(endpoint)
        if err:
            return [], Exception(f"request error: {err}")
        if status_code != 200:
            return [], Exception(f"non-200 status: {status_code}. Response: {json_response}")
            
        try:
            data = json.loads(json_response)
            total = data.get('total', 0) # Update total count
            
            for item in data.get('items', []):
                track_data = item.get('track')
                if not track_data: continue
                
                all_artists = [a['name'] for a in track_data.get('artists', [])]
                primary_artist = all_artists[0] if all_artists else ""

                track = Track(
                    Title=track_data.get('name', ''),
                    Artist=primary_artist,
                    Artists=all_artists,
                    Duration=track_data.get('duration_ms', 0) // 1000,
                    Album=track_data.get('album', {}).get('name', '')
                )
                all_tracks.append(track)
                
            offset += limit # Pagination update
            
        except json.JSONDecodeError as e:
            return [], Exception(f"failed to parse playlist JSON: {e}")
        except Exception as e:
            return [], e
            
    return all_tracks, None


def AlbumInfo(url_str: str) -> Tuple[List[Track], Optional[Exception]]:
    re_pattern = re.compile(r'open\.spotify\.com\/album\/([a-zA-Z0-9]{22})')
    matches = re_pattern.search(url_str)
    if not matches:
        return [], Exception("invalid album URL")
        
    album_id = matches.group(1)

    endpoint = f"{SPOTIFY_API_BASE}/albums/{album_id}/tracks"
    
    status_code, json_response, err = _request(endpoint)
    if err:
        return [], Exception(f"error getting album info: {err}")
    if status_code != 200:
        return [], Exception(f"non-200 status: {status_code}. Response: {json_response}")

    try:
        data = json.loads(json_response)
        tracks: List[Track] = []
        
        for item in data.get('items', []):
            all_artists = [a['name'] for a in item.get('artists', [])]
            primary_artist = all_artists[0] if all_artists else ""

            track = Track(
                Title=item.get('name', ''),
                Artist=primary_artist,
                Artists=all_artists,
                Duration=item.get('duration_ms', 0) // 1000,
                Album="" # Album name must be fetched from the album's root endpoint if needed
            )
            tracks.append(track)

        return tracks, None
        
    except json.JSONDecodeError as e:
        return [], Exception(f"failed to parse album JSON: {e}")
    except Exception as e:
        return [], e
