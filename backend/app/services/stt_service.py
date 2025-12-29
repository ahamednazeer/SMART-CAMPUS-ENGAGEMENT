import io
import os
import tempfile
from faster_whisper import WhisperModel
import asyncio
from concurrent.futures import ThreadPoolExecutor

class STTService:
    _model = None
    _executor = ThreadPoolExecutor(max_workers=1)
    
    # Model size: tiny, base (recommended), small, medium, large-v3
    MODEL_SIZE = "base"
    
    @classmethod
    def get_model(cls):
        if cls._model is None:
            # Use 'cpu' for Mac by default, 'cuda' if GPU available (not usually for Mac)
            # compute_type: int8 (fastest), float16, float32
            print(f"Loading Whisper model '{cls.MODEL_SIZE}'...")
            cls._model = WhisperModel(cls.MODEL_SIZE, device="cpu", compute_type="int8")
            print("Whisper model loaded successfully.")
        return cls._model

    @classmethod
    async def transcribe(cls, audio_bytes: bytes) -> str:
        """Transcribe audio bytes to text using local Whisper model."""
        # Run calculation in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(cls._executor, cls._transcribe_sync, audio_bytes)

    @classmethod
    def _transcribe_sync(cls, audio_bytes: bytes) -> str:
        try:
            model = cls.get_model()
            
            # WhisperModel needs a file path or a binary stream
            # We'll save to a temp file as it's more reliable for some audio formats
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                temp_audio.write(audio_bytes)
                temp_path = temp_audio.name
            
            try:
                # Transcribe
                # beam_size: 5 (default), higher = more accurate but slower
                segments, info = model.transcribe(temp_path, beam_size=5)
                
                text = ""
                for segment in segments:
                    text += segment.text + " "
                
                return text.strip()
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            print(f"STT Error: {e}")
            return f"Transcription error: {str(e)}"
