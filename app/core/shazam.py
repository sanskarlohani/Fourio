import time
import math
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
from app.models.model import Match 
from app.db.db_clients import NewDBClient
from .fingerprint import Fingerprint, TARGET_ZONE_SIZE
from app.utils.utils import GenerateUniqueID
from app.utils.logger_setup import GetLogger
from .spectrogram import Spectrogram, ExtractPeaks

def analyze_relative_timing(matches: Dict[int, List[Tuple[int, int]]]) -> Dict[int, float]:
    """
    Calculates a score based on the consistency of relative timing between sample and database.
    """
    scores: Dict[int, float] = {}
    tolerance_ms = 100  
    
    for song_id, times in matches.items():
        count = 0
        N = len(times)
        
        for i in range(N):
            for j in range(i + 1, N):
                sample_time_i, db_time_i = times[i]
                sample_time_j, db_time_j = times[j]
                
                sample_diff = abs(float(sample_time_i - sample_time_j))
                db_diff = abs(float(db_time_i - db_time_j))
                
                if math.fabs(sample_diff - db_diff) < tolerance_ms:
                    count += 1
                    
        scores[song_id] = float(count)
        
    return scores

def filter_matches(
    threshold: int,
    matches: Dict[int, List[Tuple[int, int]]],
    target_zones: Dict[int, Dict[int, int]]
) -> Dict[int, List[Tuple[int, int]]]:
    """
    Filters out songs that don't have enough verified target zones.
    """
    
    # 1. Filter out non-target zones (count < TARGET_ZONE_SIZE)
    for song_id, anchor_times in target_zones.items():
        keys_to_delete = [anchor_time for anchor_time, count in anchor_times.items() 
                          if count < TARGET_ZONE_SIZE]
        for key in keys_to_delete:
             del target_zones[song_id][key]

    filtered_matches: Dict[int, List[Tuple[int, int]]] = {}
    for song_id, zones in target_zones.items():
        # if the number of remaining valid target zones meets the threshold
        if len(zones) >= threshold:
            filtered_matches[song_id] = matches[song_id]

    return filtered_matches

# --- Main Matcher Functions ---

def FindMatchesFGP(sample_fingerprint: Dict[int, int]) -> Tuple[List[Match], float, Optional[Exception]]:
    """
    Uses the sample fingerprint (address -> sampleTime) 
    to find and score matches in the database.
    """
    start_time = time.perf_counter()
    logger = GetLogger()

    addresses: List[int] = list(sample_fingerprint.keys())

    db_client, err = NewDBClient()
    if err: 
        return None, time.perf_counter() - start_time, err
    
    # 'with'  handles  db.Close()
    with db_client: 
        m, err = db_client.GetCouples(addresses) # Dict[address, List[Couple]]
        if err: 
            return None, time.perf_counter() - start_time, err

        # songID -> [(sampleTime, dbTime)]
        matches: Dict[int, List[Tuple[int, int]]] = defaultdict(list) 
        # songID -> earliest anchor time in DB
        timestamps: Dict[int, int] = {} 
        # songID -> {timestamp: count} (Used for filterMatches)
        target_zones: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int)) 

        # process Matches and Timing
        for address, couples in m.items():
            sample_time_ms = sample_fingerprint[address]
            
            for couple in couples:
                song_id = couple.SongID
                db_time_ms = couple.AnchorTimeMs
                
                matches[song_id].append((sample_time_ms, db_time_ms))

                # find the earliest timestamp (for final match output)
                if song_id not in timestamps or db_time_ms < timestamps[song_id]:
                    timestamps[song_id] = db_time_ms

                target_zones[song_id][db_time_ms] += 1

        # Filter Matches 
        # To enable filtering: matches = filter_matches(10, matches, target_zones)

        # analyze Relative Timing (Scoring)
        scores = analyze_relative_timing(matches)

        # BATCH FETCH: Get all songs in one MongoDB query
        song_ids = list(scores.keys())
        songs_map, err = db_client.GetSongsByIDs(song_ids)
        if err:
            logger.error(f"Failed to fetch songs: {err}")
            return None, time.perf_counter() - start_time, err
        
        # Build Final Match List
        match_list: List[Match] = []
        for song_id, score in scores.items():
            song = songs_map.get(song_id)
            
            if not song:
                logger.info(f"song with ID ({song_id}) doesn't exist")
                continue

            match = Match(
                SongID=song_id,
                Title=song.Title,
                Artist=song.Artist,
                YouTubeID=song.YouTubeID,
                Timestamp=timestamps.get(song_id, 0),
                Score=score
            )
            match_list.append(match)

    # sort Matches by Score 
    match_list.sort(key=lambda m: m.Score, reverse=True)

    return match_list, time.perf_counter() - start_time, None


def FindMatches(audio_sample: List[float], audio_duration: float, sample_rate: int) -> Tuple[List[Match], float, Optional[Exception]]:
    """
    Corresponds to the Go FindMatches function (Full DSP -> Fingerprint -> Match process).
    """
    start_time = time.perf_counter()

    # 1. DSP Pipeline
    spectrogram, err = Spectrogram(audio_sample, sample_rate)
    if err: return None, time.perf_counter() - start_time, Exception(f"failed to get spectrogram of samples: {err}")

    peaks = ExtractPeaks(spectrogram, audio_duration)
    
    # 2. Fingerprinting
    sample_id_placeholder = GenerateUniqueID() 
    sample_fingerprint = Fingerprint(peaks, sample_id_placeholder) 

    # Prepare map: address (hash) -> anchorTimeMs (time in sample)
    sample_fingerprint_map: Dict[int, int] = {
        address: couple.AnchorTimeMs 
        for address, couple in sample_fingerprint.items()
    }

    # 3. Matching
    # The duration returned is the duration of FindMatchesFGP, but we return the total duration
    matches, _, err = FindMatchesFGP(sample_fingerprint_map) 

    return matches, time.perf_counter() - start_time, None