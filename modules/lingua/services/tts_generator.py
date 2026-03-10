from pathlib import Path
from ..models.lingua_config import settings
import gc
import re
import wave
import uuid
import os

class TTSGenerator:
    def __init__(self):
        # Force CPU if requested for stability, otherwise use GPU if available
        self.device = "cpu" # Default
        self.tts = None

    def get_tts(self):
        if self.tts is None:
            import torch
            from TTS.api import TTS
            
            if settings.CPU_FRIENDLY_MODE:
                self.device = "cpu"
            else:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
                
            self.tts = TTS(settings.COQUI_TTS_MODEL).to(self.device)
        return self.tts

    def generate(self, text: str, output_path: Path, speaker_wav: Path = None, language: str = "en"):
        # If disabled in config, skip
        if not settings.TTS_ENABLED:
            print("TTS Generation is disabled in config.")
            return None
            
        tts = self.get_tts()
        
        # Determine speaker
        speaker_kwarg = {}
        if speaker_wav and speaker_wav.exists():
            speaker_kwarg['speaker_wav'] = str(speaker_wav)
        elif tts.speakers:
            speaker_kwarg['speaker'] = tts.speakers[0]
            
        # Split text into manageable chunks to avoid OOM
        chunks = self._chunk_text(text, settings.TTS_MAX_CHUNK_LENGTH)
        
        chunk_files = []
        try:
            for i, chunk in enumerate(chunks):
                chunk = chunk.strip()
                if not chunk:
                    continue
                temp_chunk_path = settings.TEMP_DIR / f"chunk_{uuid.uuid4().hex}_{i}.wav"
                
                # Generate audio for the segment
                tts.tts_to_file(
                    text=chunk,
                    language=language,
                    file_path=str(temp_chunk_path),
                    **speaker_kwarg
                )
                chunk_files.append(temp_chunk_path)
                
            # Merge chunks
            if chunk_files:
                self._merge_wavs(chunk_files, output_path)
        finally:
            # Clean up temp chunks
            for cf in chunk_files:
                if cf.exists():
                    try:
                        os.remove(cf)
                    except Exception as e:
                        print(f"Failed to remove temp chunk {cf}: {e}")
                        
            # Aggressive memory cleanup option
            if settings.CPU_FRIENDLY_MODE:
                self._cleanup_memory()
                
        return output_path

    def _chunk_text(self, text: str, max_length: int) -> list:
        """
        Splits text by sentence boundaries (e.g. . ! ?) keeping chunks under max_length 
        if possible, to balance memory usage for XTTS.
        """
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # If a single sentence is larger than max_length, it gets its own chunk anyway
                current_chunk = sentence + " "
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    def _merge_wavs(self, wav_paths: list, output_path: Path):
        """Concatenate multiple wav files into one final output in a streaming way."""
        if not wav_paths:
            return

        try:
            # Read params from the first file
            params = None
            with wave.open(str(wav_paths[0]), 'rb') as first_wav:
                params = first_wav.getparams()

            if params:
                with wave.open(str(output_path), 'wb') as output:
                    output.setparams(params)
                    for wav_file in wav_paths:
                        with wave.open(str(wav_file), 'rb') as w:
                            while True:
                                # Read in 1MB chunks to avoid memory spikes
                                frames = w.readframes(1024 * 1024)
                                if not frames:
                                    break
                                output.writeframes(frames)
        except Exception as e:
            print(f"Error merging wavs in streaming mode: {e}")
            raise

    def _cleanup_memory(self):
        import torch
        # Force garbage collection to free large model tensors
        if self.tts is not None:
            del self.tts
            self.tts = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
