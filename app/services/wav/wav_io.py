import struct
import base64
import json
import subprocess
import os
import io
import time
from typing import List, Tuple, Optional, Any, NamedTuple, Dict
from pathlib import Path
import numpy as np
from app.models.model import RecordData 
from app.utils.logger_setup import GetLogger
from app.utils.file_io import DeleteFile, CreateFolder
from wav_converter import ReformatWAV 

WAV_HEADER_SIZE = 44 # Standard size of a minimal WAV header

# --- Data Structures ---
class WavInfo(NamedTuple):
    Channels: int
    SampleRate: int
    Data: bytes      # audio bytes
    Duration: float

#complex FFmpeg/FFprobe metadata structure
FFmpegMetadata = Dict[str, Any]

def _write_wav_header(f: io.FileIO, data_size: int, sample_rate: int, channels: int, bits_per_sample: int) -> Optional[Exception]:
    """
     writes the 44-byte WAV header.
    """
    if data_size % channels != 0:
        return Exception("Data size not divisible by channels")

    subchunk1_size = 16 
    bytes_per_sample = bits_per_sample // 8
    block_align = channels * bytes_per_sample
    subchunk2_size = data_size

    # Byte Rate = SampleRate * Channels * BytesPerSample
    bytes_per_sec = sample_rate * channels * bytes_per_sample
    chunk_size = 36 + data_size # 4 bytes (header size) + 36 bytes (metadata) + data size

    # Use struct.pack to write the header in Little Endian format ('<')
    # Format string: 4s I 4s 4s I H H I I H H 4s I (s=string, I=uint32, H=uint16)
    try:
        header = struct.pack('<4sI4s4sIHHIHH4sI', 
            b'RIFF', chunk_size, b'WAVE', 
            b'fmt ', subchunk1_size, 
            1, # AudioFormat (1=PCM)
            channels, sample_rate, bytes_per_sec, block_align, bits_per_sample, 
            b'data', subchunk2_size
        )
        f.write(header)
        return None
    except Exception as e:
        return e

def WriteWavFile(filename: str, data: bytes, sample_rate: int, channels: int, bits_per_sample: int) -> Optional[Exception]:
    """
    creates and writes a complete WAV file.
    """
    if sample_rate <= 0 or channels <= 0 or bits_per_sample <= 0:
        return Exception(
            f"values must be greater than zero (sampleRate: {sample_rate}, channels: {channels}, bitsPerSample: {bits_per_sample})"
        )

    try:
        with open(filename, 'wb') as f:
            # 1. Write Header
            err = _write_wav_header(f, len(data), sample_rate, channels, bits_per_sample)
            if err: return err

            # 2. Write Data
            f.write(data)
        return None
    except Exception as e:
        return e

def ReadWavInfo(filename: str) -> Tuple[Optional[WavInfo], Optional[Exception]]:
    """
    reads and validates the WAV header.
    """
    try:
        # 1. Read entire file contents
        data = Path(filename).read_bytes()

        if len(data) < WAV_HEADER_SIZE:
            return None, Exception("invalid WAV file size (too small)")

        # 2. Read header chunks using struct.unpack
        # Format string: 4s I 4s 4s I H H I I H H 4s I 
        header_data = data[:WAV_HEADER_SIZE]
        header = struct.unpack('<4sI4s4sIHHIHH4sI', header_data)
        
        chunk_id = header[0].decode('ascii')
        file_format = header[2].decode('ascii')
        audio_format = header[5]
        num_channels = header[6]
        sample_rate = header[7]
        bits_per_sample = header[11]
        subchunk2_size = header[13]

        if chunk_id != "RIFF" or file_format != "WAVE" or audio_format != 1:
            return None, Exception("invalid WAV header format (not RIFF/WAVE/PCM)")

        # 3. Extract information
        raw_audio_data = data[WAV_HEADER_SIZE:]
        
        # 4. Calculate Duration (assumes 16-bit PCM for simple duration calculation)
        if bits_per_sample == 16:
            # Duration = TotalBytes / (Channels * BytesPerSample * SampleRate)
            duration = float(len(raw_audio_data)) / float(num_channels * 2 * sample_rate)
        else:
            return None, Exception("unsupported bits per sample format (only 16-bit supported for reading)")

        info = WavInfo(
            Channels=num_channels,
            SampleRate=sample_rate,
            Data=raw_audio_data,
            Duration=duration
        )
        return info, None

    except Exception as e:
        return None, e


def WavBytesToSamples(input_bytes: bytes) -> Tuple[Optional[List[float]], Optional[Exception]]:
    """
    converts 16-bit PCM bytes to float64 samples [-1.0, 1.0].
    """
    if len(input_bytes) % 2 != 0:
        return None, Exception("invalid input length (must be multiple of 2 for 16-bit samples)")

    # Use numpy for extremely fast byte-to-float conversion (preferred over Python struct loop)
    try:
        # Interpret bytes as Little-Endian signed 16-bit integers
        samples_int16 = np.frombuffer(input_bytes, dtype='<i2') # <i2 = Little Endian, signed 16-bit
        
        # Scale the signed integers to the normalized float range [-1.0, 1.0]
        samples_float64 = samples_int16.astype(np.float64) / 32768.0
        
        return samples_float64.tolist(), None
    except Exception as e:
        return None, e

# ----------------------------------------------------------------------
# --- FFprobe Metadata and Processing Pipeline ---

def GetMetadata(file_path: str) -> Tuple[FFmpegMetadata, Optional[Exception]]:
    """
    Retrieves structured metadata using ffprobe.
    """
    metadata: FFmpegMetadata = {}

    try:
        # Use subprocess to call ffprobe and capture JSON output
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json", 
            "-show_format", "-show_streams", file_path
        ]
        
        process = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Unmarshal/Parse JSON output
        metadata = json.loads(process.stdout)
        # convert all keys of the Tags map to lowercase      
        return metadata, None
    except FileNotFoundError:
        return {}, Exception("ffprobe command not found. Ensure ffprobe is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        return {}, Exception(f"Failed to run ffprobe: {e.cmd}. Output: {e.stderr}")
    except json.JSONDecodeError as e:
        return {}, Exception(f"Failed to parse ffprobe JSON output: {e}")


def ProcessRecording(rec_data: RecordData, save_recording: bool) -> Tuple[Optional[List[float]], Optional[Exception]]:
    """
    Corresponds to the Go ProcessRecording function.
    Decodes base64 audio data, saves it as a temporary WAV, reformats it to mono, and returns float samples.
    """
    logger = GetLogger()
    
    # 1. Decode Base64 Audio
    try:
        decoded_audio_data = base64.b64decode(rec_data.Audio)
    except Exception as e:
        return None, e

    # 2. Define Temporary File Paths
    now = time.localtime()
    file_name = f"{now.tm_sec:02d}_{now.tm_min:02d}_{now.tm_hour:02d}_{now.tm_mday:02d}_{now.tm_mon:02d}_{now.tm_year}.wav"
    tmp_dir = "tmp"
    
    # Ensure temporary directory exists
    err = CreateFolder(tmp_dir)
    if err: return None, err
    
    file_path = os.path.join(tmp_dir, file_name)
    
    # 3. Write Initial WAV File
    # Note: Go used recData.SampleSize for bits_per_sample
    err = WriteWavFile(file_path, decoded_audio_data, rec_data.SampleRate, rec_data.Channels, rec_data.SampleSize)
    if err:
        DeleteFile(file_path)
        return None, err

    # 4. Reformat (Force to Mono, 1 channel)
    reformated_wav_file, err = ReformatWAV(file_path, 1)
    if err:
        DeleteFile(file_path)
        return None, err
    
    # Ensure temp file is cleaned up after reformatting
    DeleteFile(file_path)

    # 5. Read Samples and Extract Data
    wav_info, err = ReadWavInfo(reformated_wav_file)
    if err: 
        DeleteFile(reformated_wav_file)
        return None, err
        
    samples, err = WavBytesToSamples(wav_info.Data)
    if err: 
        DeleteFile(reformated_wav_file)
        return None, err
    
    # 6. Save/Cleanup Logic
    if save_recording:
        recordings_dir = "recordings"
        err = CreateFolder(recordings_dir)
        if err:
            logger.error(f"Failed to create recordings folder: {err}")
        
        # Rename/Move the file
        new_file_path = os.path.join(recordings_dir, os.path.basename(reformated_wav_file))
        err = os.rename(reformated_wav_file, new_file_path)
        if err:
            logger.error(f"Failed to move file {reformated_wav_file} to {new_file_path}: {err}")
    else:
        # Delete the reformatted file if we don't need to save it
        DeleteFile(reformated_wav_file)

    return samples, None