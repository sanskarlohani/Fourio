import numpy as np
import math
from typing import List, Tuple, Optional
# from .fft import FFT 
from .fft import NumPy_FFT as FFT 
from app.models.model import Peak, MaxPeakInfo

# TODO: For high-quality filtering and resampling would use scipy.signal,



# --- Constants (Corresponds to Go const block) ---
DSP_RATIO = 4
FREQ_BIN_SIZE = 1024
MAX_FREQ = 5000.0  # 5kHz (Low-pass filter cutoff)
HOP_SIZE = FREQ_BIN_SIZE // 32 # 1024 / 32 = 32

def LowPassFilter(cutoff_frequency: float, sample_rate: float, input_data: List[float]) -> List[float]:
    """
    It attenuates high frequencies while allowing low frequencies to pass through, 
    acting as a smoother or integrator for signals
    It uses the transfer function H(s) = 1 / (1 + sRC), where RC is the time constant.
    """
    rc = 1.0 / (2 * math.pi * cutoff_frequency)
    dt = 1.0 / sample_rate
    alpha = dt / (rc + dt)

    input_np = np.array(input_data)
    filtered_signal = np.zeros_like(input_np)
    prev_output = 0.0

    for i, x in enumerate(input_np):
        if i == 0:
            filtered_signal[i] = x * alpha
        else:
            filtered_signal[i] = alpha * x + (1 - alpha) * prev_output

        prev_output = filtered_signal[i]
        
    return filtered_signal.tolist()

def Downsample(input_data: List[float], original_sample_rate: int, target_sample_rate: int) -> Tuple[List[float], Optional[Exception]]:
    """
    According to the Nyquist-Shannon sampling theorem, 
    we only need a sample rate slightly more than twice the highest frequency we care about. 
    Since we've filtered out everything above 5kHz, 
    a sample rate of around 10-12kHz is sufficient.

    help speed up the FFT and reduce the memory usage.
    """
    if target_sample_rate <= 0 or original_sample_rate <= 0:
        return None, Exception("sample rates must be positive")
    
    if target_sample_rate > original_sample_rate:
        return None, Exception("target sample rate must be less than or equal to original sample rate")

    ratio = original_sample_rate / target_sample_rate

    if ratio <= 0 or not ratio.is_integer():
        return None, Exception("invalid ratio calculated from sample rates (must be an integer ratio)")

    ratio = int(ratio)
    resampled: List[float] = [] 
    input_np = np.array(input_data)
    N = len(input_np)
    
    for i in range(0, N, ratio):
        block = input_np[i : i + ratio]
        
        if len(block) > 0:
            avg = np.sum(block) / len(block)
            resampled.append(avg)
            
    return resampled, None

def Spectrogram(sample: List[float], sample_rate: int) -> Tuple[List[List[complex]], Optional[Exception]]:
    print(f"[Spectrogram DEBUG] Starting DSP pipeline. Input size: {len(sample)} samples.")
    filtered_sample = LowPassFilter(MAX_FREQ, float(sample_rate), sample)
    print(f"[Spectrogram DEBUG] Low-pass filter applied. Output size: {len(filtered_sample)} samples.")
    # here we downsample the audio (44100 -> 11025)
    target_sample_rate = sample_rate // DSP_RATIO
    print(f"[Spectrogram DEBUG] Target sample rate: {target_sample_rate}")
    downsampled_sample, err = Downsample(filtered_sample, sample_rate, target_sample_rate)
    print(f"[Spectrogram DEBUG] Downsampled audio. Output size: {len(downsampled_sample)} samples.")
    if err:
        return None, Exception(f"couldn't downsample audio sample: {err}")
    if not downsampled_sample:
        return [], None
        
    downsampled_np = np.array(downsampled_sample)
  
    window_shift = FREQ_BIN_SIZE - HOP_SIZE
    if window_shift <= 0: return None, Exception("Invalid hop size calculation")
    
    total_samples = len(downsampled_np)
    print(f"[Spectrogram DEBUG] Total samples after downsampling: {total_samples}")
    if total_samples < FREQ_BIN_SIZE: return [], None

    # num_windows based on the overlap (length - window_size) / hop_size + 1
    num_windows = (total_samples - FREQ_BIN_SIZE) // HOP_SIZE + 1
    
    spectrogram: List[List[complex]] = [[]] * num_windows
    print(f"[Spectrogram DEBUG] Calculated {num_windows} windows for STFT.")
    print(f"[Spectrogram DEBUG] Starting heavy FFT loop...")
  
    # a general Hanning/Hamming-like window (specifically, the 0.54/0.46 is Hamming).
    window_indices = np.arange(FREQ_BIN_SIZE)
    window_func = 0.54 - 0.46 * np.cos(2 * math.pi * window_indices / (FREQ_BIN_SIZE - 1))

    # STFT (Short-Time Fourier Transform)
    for i in range(num_windows):
        start = i * HOP_SIZE
        end = start + FREQ_BIN_SIZE
        
        bin_data = downsampled_np[start:end]
        windowed_bin = bin_data * window_func
        spectrogram[i] = FFT(windowed_bin.tolist())
        
    return spectrogram, None




#frequency bin ranges for peak extraction
BANDS = [
    (0, 10), (10, 20), (20, 40), (40, 80), 
    (80, 160), (160, 512)
]
def ExtractPeaks(spectrogram: List[List[complex]], audio_duration: float) -> List[Peak]:
    """
    this specific method of peak extraction is called 
    "Max-Magnitude Per Frequency Band" extraction
    """
    if len(spectrogram) < 1:
        return []

    peaks: List[Peak] = []
    bin_duration = audio_duration / float(len(spectrogram))

    for bin_idx, bin_data in enumerate(spectrogram):
        bin_band_maxies: List[MaxPeakInfo] = []
        
        for band_min, band_max in BANDS:
            max_mag = 0.0
            max_info = MaxPeakInfo(0.0, complex(0,0), 0)
          
            band_slice = bin_data[band_min:band_max]
            
            for idx, freq in enumerate(band_slice):
                magnitude = abs(freq)
                
                if magnitude > max_mag:
                    max_mag = magnitude
                    freq_idx = band_min + idx 
                    max_info = MaxPeakInfo(magnitude, freq, freq_idx)
                    
            if max_mag > 0.0: 
                bin_band_maxies.append(max_info)

        if not bin_band_maxies:
            continue

        max_mags = [info.max_mag for info in bin_band_maxies]
        avg_magnitude = sum(max_mags) / len(max_mags)

        for info in bin_band_maxies:
            if info.max_mag > avg_magnitude: 
                #TODO
                # Go: peakTimeInBin := freqIndices[i] * binDuration / float64(len(bin))
                # Note: Go's logic seems to incorrectly use 'freqIndices[i]' which is a frequency index,
                # to calculate a time offset *within* the bin. In standard DSP, the time offset is 
                # generally considered zero, or based on the bin center. 
                # Translating the Go logic directly:
                
                # The freqIdx is used as an arbitrary coefficient in the Go code.
                peak_time_in_bin = float(info.freq_idx) * bin_duration / float(len(bin_data))

                # Calculate the absolute time of the peak
                # Go: peakTime := float64(binIdx)*binDuration + peakTimeInBin
                peak_time = float(bin_idx) * bin_duration + peak_time_in_bin

                peaks.append(Peak(Time=peak_time, Freq=info.max_freq))

    return peaks