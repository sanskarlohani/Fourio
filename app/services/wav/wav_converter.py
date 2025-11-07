import os
import subprocess
import pathlib
from typing import Tuple, Optional,List

from utils.file_io import MoveFile 

DEFAULT_SAMPLE_RATE = "44100"  # in Hz
AUDIO_CODEC = "pcm_s16le"      # 16-bit Signed Little-Endian PCM (WAV Standard)


def validate_channels(channels: int) -> int:
    if channels < 1 or channels > 2:
        return 1
    return channels

def _run_ffmpeg_command(command_args: List[str]) -> Optional[Exception]:
    """Helper to execute FFmpeg and handle output/errors."""
    try:
        process = subprocess.run(
            ["ffmpeg"] + command_args,
            check=True,                 # Raises CalledProcessError on non-zero exit code
            capture_output=True,        # Captures stdout and stderr
            text=True
        )
        return None
    except FileNotFoundError:
        return Exception("FFmpeg command not found. Ensure FFmpeg is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        output_str = f"STDOUT: {e.stdout}\nSTDERR: {e.stderr}"
        return Exception(f"Failed to convert audio: {e.cmd}. Output: {output_str}")
    except Exception as e:
        return e


def ConvertToWAV(input_file_path: str, channels: int) -> Tuple[Optional[str], Optional[Exception]]:
    """
    Converts any input audio file to standardized WAV format (44100Hz, 16-bit PCM).
    """
    input_path = pathlib.Path(input_file_path)
    if not input_path.exists():
        return None, Exception(f"Input file does not exist: {input_file_path}")

    target_channels = validate_channels(channels)
    
    # 1. Define Output Paths (using pathlib for clean file operations)
    output_file_path = input_path.with_suffix(".wav")
    tmp_file_path = input_path.parent / f"tmp_{output_file_path.name}"
    
    # cleaned up temp files
    def cleanup():
        if tmp_file_path.exists():
            os.remove(tmp_file_path)
            
    try:
        # FFmpeg Command Construction 
        command_args = [
            "-y",                                   # Overwrite output files without asking
            "-i", str(input_path),                  # Input file
            "-c:a", AUDIO_CODEC,                    # Set audio codec to 16-bit PCM
            "-ar", DEFAULT_SAMPLE_RATE,             # Set sample rate to 44.1 kHz
            "-ac", str(target_channels),            # Set channels (1 or 2)
            str(tmp_file_path)                      # Output to temporary file
        ]

        err = _run_ffmpeg_command(command_args)
        if err:
            cleanup()
            return None, err

        # 2. Rename the temporary file to the final output file (using MoveFile utility)
        err = MoveFile(str(tmp_file_path), str(output_file_path))
        if err:
            return None, Exception(f"Failed to rename temporary file: {err}")

        return str(output_file_path), None
    
    except Exception as e:
        cleanup()
        return None, e


def ReformatWAV(input_file_path: str, channels: int) -> Tuple[Optional[str], Optional[Exception]]:
    """
    Converts a WAV file to mono or stereo (primarily used for forcing mono).
    """
    input_path = pathlib.Path(input_file_path)
    if not input_path.exists():
        return None, Exception(f"Input file does not exist: {input_file_path}")

    target_channels = validate_channels(channels)

    # Define Output Path (using rfm suffix as in Go)
    output_file_path = input_path.parent / f"{input_path.stem}rfm.wav"

    # FFmpeg Command Construction
    command_args = [
        "-y", 
        "-i", str(input_path),
        "-c:a", AUDIO_CODEC, 
        "-ar", DEFAULT_SAMPLE_RATE, 
        "-ac", str(target_channels), 
        str(output_file_path)
    ]
    
    err = _run_ffmpeg_command(command_args)
    if err:
        return None, err

    return str(output_file_path), None