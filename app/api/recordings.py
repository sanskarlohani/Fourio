from datetime import datetime
from typing import Dict
from fastapi import APIRouter, HTTPException
from app.models.model import RecordData
from app.utils.logger_setup import GetLogger
from app.utils.file_io import CreateFolder
from app.services.wav.wav_io import WriteWavFile
import base64

router = APIRouter(prefix="/recordings", tags=["recordings"])
logger = GetLogger()

# --------------------------------------------------------------------
# POST /recordings/save ( handleNewRecording)
# --------------------------------------------------------------------
@router.post("/save", response_model=Dict[str, str])
async def handle_new_recording(rec_data: RecordData):
    """
    Saves new recorded audio snippet (base64 encoded) to a WAV file.
    """
    try:
        # 1. Setup File Path
        err = CreateFolder("recordings")
        if err:
            logger.error(f"Failed to create recordings folder: {err}")
            raise HTTPException(500, detail="Failed to create recording folder")

        now = datetime.now()
        file_name = f"{now.second:02d}_{now.minute:02d}_{now.hour:02d}_{now.day:02d}_{now.month:02d}_{now.year}.wav"
        file_path = f"recordings/{file_name}"

        # 2. Decode Audio Data
        try:
            decoded_audio_data = base64.b64decode(rec_data.Audio)
        except Exception as e:
            logger.error(f"Failed to decode base64 audio: {e}")
            raise HTTPException(400, detail="Invalid base64 audio data.")

        # 3. Write WAV File
        err = WriteWavFile(file_path, decoded_audio_data, rec_data.SampleRate, rec_data.Channels, rec_data.SampleSize)
        
        if err:
            logger.error(f"Failed write wav file: {err}")
            raise HTTPException(500, detail="Failed to write WAV file.")

        return {"message": "Recording saved successfully", "path": file_path}

    except Exception as e:
        logger.error(f"Unexpected error processing recording: {e}")
        raise HTTPException(500, detail="Internal error processing audio data.")