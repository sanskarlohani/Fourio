import math
from typing import List
import numpy as np

# Note: For better understanding of the FFT algorithm, refer to this video:
# https://www.youtube.com/watch?v=spUNpyF58BY

def _recursive_fft(complex_array: List[complex]) -> List[complex]:
    # Time complexity: O(N log N)
    N = len(complex_array)
    
    #base case
    if N <= 1:
        return complex_array

    # divide into even and odd parts
    even = [complex_array[2 * i] for i in range(N // 2)]
    odd = [complex_array[2 * i + 1] for i in range(N // 2)]

    even = _recursive_fft(even)
    odd = _recursive_fft(odd)

    # butterfly operation
    fft_result = [complex(0, 0)] * N
    
    for k in range(N // 2):
        # (W_N^k): e^(-i * 2 * pi * k / N)
        angle = -2 * math.pi * k / N
        t = complex(math.cos(angle), math.sin(angle))
        
        # butterfly computation
        fft_result[k] = even[k] + t * odd[k]
        fft_result[k + N // 2] = even[k] - t * odd[k]

    return fft_result

# converts a time-domain signal (real numbers) -> frequency domain.
def FFT(input_data: List[float]) -> List[complex]:
  
    complex_array = [complex(v, 0) for v in input_data]
    
    return _recursive_fft(complex_array)

def NumPy_FFT(input_data: np.ndarray) -> np.ndarray:
    np_result = np.fft.fft(input_data)
    return np_result