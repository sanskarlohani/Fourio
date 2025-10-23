import time
import math
from typing import List, Dict, Tuple, Optional
from models.model import Match 
from db.db_clients import NewDBClient
from fingerprint import Fingerprint, TARGET_ZONE_SIZE
from utils.utils import GenerateUniqueID
from utils.logger_setup import GetLogger
from spectrogram import Spectrogram, ExtractPeaks


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
    Corresponds to the Go filterMatches function.
    Filters out songs that don't have enough verified target zones.
    """
    
    # 1. Filter out non-target zones (count < TARGET_ZONE_SIZE)
    # Note: Using list() of items allows safe deletion while iterating over a copy
    for song_id, anchor_times in target_zones.items():
        keys_to_delete = [anchor_time for anchor_time, count in anchor_times.items() 
                          if count < TARGET_ZONE_SIZE]
        for key in keys_to_delete:
             del target_zones[song_id][key]

    # 2. Filter matches based on the number of remaining target zones
    filtered_matches: Dict[int, List[Tuple[int, int]]] = {}
    for song_id, zones in target_zones.items():
        # Check if the number of remaining valid target zones meets the threshold
        if len(zones) >= threshold:
            filtered_matches[song_id] = matches[song_id]

    return filtered_matches

# -----------------------------------------------------------------------------
# --- Main Matcher Functions ---

def FindMatchesFGP(sample_fingerprint: Dict[int, int]) -> Tuple[List[Match], float, Optional[Exception]]:
    """
    Corresponds to the Go FindMatchesFGP function.
    Uses the sample fingerprint (address -> sampleTime) to find and score matches in the database.
    """
    start_time = time.perf_counter()
    logger = GetLogger()

    # 1. Prepare Addresses for DB Query
    addresses: List[int] = list(sample_fingerprint.keys())

    db_client, err = NewDBClient()
    if err: return None, time.perf_counter() - start_time, err
    
    # Python's 'with' statement handles defer db.Close()
    with db_client: 
        m, err = db_client.GetCouples(addresses) # Dict[address, List[Couple]]
        if err: return None, time.perf_counter() - start_time, err

        # songID -> [(sampleTime, dbTime)]
        matches: Dict[int, List[Tuple[int, int]]] = {} 
        # songID -> earliest anchor time in DB
        timestamps: Dict[int, int] = {} 
        # songID -> {timestamp: count} (Used for filterMatches)
        target_zones: Dict[int, Dict[int, int]] = {} 

        # 2. Process Matches and Timing
        for address, couples in m.items():
            sample_time_ms = sample_fingerprint[address]
            
            for couple in couples:
                song_id = couple.SongID
                db_time_ms = couple.AnchorTimeMs
                
                # Record the time pair: (sampleTime, dbTime)
                matches.setdefault(song_id, []).append((sample_time_ms, db_time_ms))

                # Find the earliest timestamp (for final match output)
                if song_id not in timestamps or db_time_ms < timestamps[song_id]:
                    timestamps[song_id] = db_time_ms

                # Count occurrences for target zone filtering
                target_zones.setdefault(song_id, {}).setdefault(db_time_ms, 0)
                target_zones[song_id][db_time_ms] += 1

        # 3. Filter Matches (The Go code had this commented out)
        # To enable filtering: matches = filter_matches(10, matches, target_zones)

        # 4. Analyze Relative Timing (Scoring)
        scores = analyze_relative_timing(matches)
        match_list: List[Match] = []

        # 5. Build Final Match List
        for song_id, score in scores.items():
            song, song_exists, err = db_client.GetSongByID(song_id)
            
            if not song_exists:
                logger.info(f"song with ID ({song_id}) doesn't exist")
                continue
            if err:
                logger.info(f"failed to get song by ID ({song_id}): {err}")
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

    # 6. Sort Matches by Score (Descending)
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