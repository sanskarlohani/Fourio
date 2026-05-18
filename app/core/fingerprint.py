from typing import Dict, List
from app.models.model import Couple,Peak
import time
# --- Fingerprint Address Bit Allocation ---
# The 32-bit address (hash) is constructed by allocating specific bit ranges
# to the frequency of the anchor peak, the frequency of the target peak, 
# and the time difference (delta time) between them.
#
# Component         | Bit Range | Size (Bits) | Shift Value (Bits Left)
# ------------------|-----------|-------------|------------------------
# Anchor Frequency  | 23 - 31   | 9           | 23
# Target Frequency  | 14 - 22   | 9           | 14
# Delta Time (ms)   | 0 - 13    | 14          | 0
# ------------------------------------------------------------------------

MAX_FREQ_BITS  = 9
MAX_DELTA_BITS = 14
TARGET_ZONE_SIZE = 5

# Define the bit masks/shifts based on the allocation:
ANCHOR_FREQ_SHIFT = 23
TARGET_FREQ_SHIFT = 14
# Delta time uses the lowest bits, so the shift value is 0.

def create_address(anchor: Peak, target: Peak) -> int:
    # extract freq
    anchor_freq = int(anchor.Freq.real)
    target_freq = int(target.Freq.real)
    # convert to milliseconds
    delta_ms = int((target.Time - anchor.Time) * 1000)
    
    address = (anchor_freq << ANCHOR_FREQ_SHIFT) | (target_freq << TARGET_FREQ_SHIFT) | delta_ms
    return address


def Fingerprint(peaks: List[Peak], songID: int) -> Dict[int, Couple]:
    """
    generates fingerprints from peaks using the 'target zone' method.
    """
    # start_time = time.perf_counter()
    fingerprints: Dict[int, Couple] = {}

    for i, anchor in enumerate(peaks):
        end_index = min(len(peaks), i + TARGET_ZONE_SIZE + 1)
        
        for j in range(i + 1, end_index):
            target = peaks[j]

            address = create_address(anchor, target)
            anchor_time_ms = int(anchor.Time * 1000)

            fingerprints[address] = Couple(
                AnchorTimeMs=anchor_time_ms, 
                SongID=songID
            )
    # end_time = time.perf_counter()
    # print(f"Time taken for fingerprinting: {end_time - start_time}")       
    return fingerprints