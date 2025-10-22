import numpy as np
import math
from typing import List, Tuple, Optional
from fft import FFT 
# from fft import NumPy_FFT as FFT 


# TODO: For high-quality filtering and resampling would use scipy.signal,



# --- Constants (Corresponds to Go const block) ---
DSP_RATIO = 4
FREQ_BIN_SIZE = 1024
MAX_FREQ = 5000.0  # 5kHz (Low-pass filter cutoff)
HOP_SIZE = FREQ_BIN_SIZE // 32 # 1024 / 32 = 32

def LowPassFilter(cutoff_frequency: float, sample_rate: float, input_data: List[float]) -> List[float]:
    """
    LowPassFilter is a first-order low-pass filter that attenuates high
    frequencies above the cutoffFrequency.
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
    Corresponds to the Go Downsample function (simple block averaging).
    """
    if target_sample_rate <= 0 or original_sample_rate <= 0:
        return None, Exception("sample rates must be positive")
    if target_sample_rate > original_sample_rate:
        return None, Exception("target sample rate must be less than or equal to original sample rate")

    ratio = original_sample_rate / target_sample_rate
    if ratio <= 0 or not ratio.is_integer():
        # In the Go code, ratio is an integer division, but here it must result in an integer
        # for simple block averaging to work cleanly.
        return None, Exception("invalid ratio calculated from sample rates (must be an integer ratio)")

    ratio = int(ratio)
    
    resampled: List[float] = []
    
    # Simple block averaging downsampling (decimation)
    input_np = np.array(input_data)
    N = len(input_np)
    
    for i in range(0, N, ratio):
        # Go's start:end slice equivalent is a NumPy slice
        block = input_np[i : i + ratio]
        
        # Go's sum/avg calculation equivalent
        if len(block) > 0:
            avg = np.sum(block) / len(block)
            resampled.append(avg)
            
    return resampled, None

def Spectrogram(sample: List[float], sample_rate: int) -> Tuple[List[List[complex]], Optional[Exception]]:
    """
    Corresponds to the Go Spectrogram function, performing STFT.
    """
    
    # 1. Pre-processing: Filter and Downsample
    # Note: Using float(sample_rate) for consistency with Go's float64 cast
    filtered_sample = LowPassFilter(MAX_FREQ, float(sample_rate), sample)

    # Note: Downsample target is sampleRate/dspRatio, which is 4 in your code (e.g., 44100 -> 11025)
    target_sample_rate = sample_rate // DSP_RATIO
    downsampled_sample, err = Downsample(filtered_sample, sample_rate, target_sample_rate)
    
    if err:
        return None, Exception(f"couldn't downsample audio sample: {err}")
    
    if not downsampled_sample:
        return [], None
        
    downsampled_np = np.array(downsampled_sample)
    
    # 2. Setup STFT Parameters
    # Go: numOfWindows := len(downsampledSample) / (freqBinSize - hopSize)
    window_shift = FREQ_BIN_SIZE - HOP_SIZE
    if window_shift <= 0: return None, Exception("Invalid hop size calculation")
    
    # Calculate number of windows, ensuring at least one full window is covered
    total_samples = len(downsampled_np)
    if total_samples < FREQ_BIN_SIZE: return [], None

    # Calculate num_windows based on the overlap (length - window_size) / hop_size + 1
    num_windows = (total_samples - FREQ_BIN_SIZE) // HOP_SIZE + 1
    
    spectrogram: List[List[complex]] = [[]] * num_windows

    # 3. Generate Window (Hamming/Hann equivalent)
    # Go: 0.54 - 0.46*math.Cos(2*math.Pi*float64(i)/(float64(freqBinSize)-1))
    # This is a general Hanning/Hamming-like window (specifically, the 0.54/0.46 is Hamming).
    window_indices = np.arange(FREQ_BIN_SIZE)
    window_func = 0.54 - 0.46 * np.cos(2 * math.pi * window_indices / (FREQ_BIN_SIZE - 1))

    # 4. Perform STFT (Short-Time Fourier Transform)
    for i in range(num_windows):
        start = i * HOP_SIZE
        end = start + FREQ_BIN_SIZE
        
        # Extract the segment (bin)
        bin_data = downsampled_np[start:end]
        
        # Apply window (element-wise multiplication)
        # Go: bin[j] *= window[j]
        windowed_bin = bin_data * window_func
        
        # Perform FFT (using the translated recursive function)
        spectrogram[i] = FFT(windowed_bin.tolist())
        
    return spectrogram, None