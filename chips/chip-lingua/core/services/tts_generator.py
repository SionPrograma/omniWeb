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

    def _normalize_text(self, text: str) -> str:
        """
        Transforms markdown and technical patterns into natural human speech.
        """
        if not text:
            return ""

        # 1. Remove Markdown syntax
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold **text**
        text = re.sub(r'__([^_]+)__', r'\1', text)      # Bold __text__
        text = re.sub(r'`([^`]+)`', r'\1', text)        # Inline code `text`
        text = re.sub(r'#+\s+', '', text)               # Headers #
        text = re.sub(r'[-*]\s+', ' ', text)            # Bullets at start

        # 2. Normalize technical paths (backend/core/...)
        def path_replacer(match):
            path = match.group(0)
            # Remove extension
            path = re.sub(r'\.(py|js|ts|css|html|md|json)$', '', path)
            # Replace separators with space or " de " contextually
            parts = re.split(r'[\\/]', path)
            if len(parts) > 1:
                # If it looks like a deep path, summarize
                # "backend/core/ai_host" -> "módulo ai host del backend"
                if len(parts) > 3:
                    return f"el módulo {parts[-1].replace('_', ' ')} de {parts[0]}"
                return " de ".join(reversed([p.replace('_', ' ') for p in parts]))
            return path.replace('_', ' ')

        # Detect paths with / or \
        text = re.sub(r'\b[\w\-\.\\]+[\\/][\w\-\.\\/]+\b', path_replacer, text)
        
        # 3. Clean up remaining underscores and miscellaneous symbols
        text = text.replace('_', ' ')
        text = text.replace('*', '')  # Just in case
        text = re.sub(r'\s+', ' ', text) # Collapse spaces

        return text.strip()

    def generate(self, text: str, output_path: Path, job_id: str, speaker_wav: Path = None, language: str = "en"):
        # If disabled in config, skip
        if not settings.TTS_ENABLED:
            print("TTS Generation is disabled in config.")
            return None
            
        # Normalize for natural speech
        original_text = text
        text = self._normalize_text(text)
        
        tts = self.get_tts()
        
        # Determine speaker
        speaker_kwarg = {}
        if speaker_wav and speaker_wav.exists():
            # Ensure path is string for TTS library
            speaker_kwarg['speaker_wav'] = str(speaker_wav.absolute())
        elif tts.speakers:
            speaker_kwarg['speaker'] = tts.speakers[0]
            
        # Split text into manageable chunks to avoid OOM
        # XTTS v2 struggles with > 250 characters usually
        chunks = self._chunk_text(text, settings.TTS_MAX_CHUNK_LENGTH)
        
        print(f"[TTS] Generating {len(chunks)} chunks for {len(text)} characters...")
        
        chunk_files = []
        try:
            for i, chunk in enumerate(chunks):
                chunk = chunk.strip()
                if not chunk or len(chunk) < 2: # Skip empty or too short chunks
                    continue
                
                # Prefix with job_id for consolidated cleanup
                temp_chunk_path = settings.TEMP_DIR / f"{job_id}_chunk_{i}.wav"
                
                # Generate audio for the segment
                try:
                    tts.tts_to_file(
                        text=chunk,
                        language=language,
                        file_path=str(temp_chunk_path),
                        **speaker_kwarg
                    )
                    if temp_chunk_path.exists():
                        chunk_files.append(temp_chunk_path)
                    else:
                        print(f"[TTS] Warning: Chunk {i} failed to generate file.")
                except Exception as chunk_e:
                    print(f"[TTS] Error generating chunk {i}: {chunk_e}")
                    # Continue with other chunks if possible
                
            # Merge chunks
            if chunk_files:
                self._merge_wavs(chunk_files, output_path)
            else:
                print("[TTS] No audio chunks were successfully generated.")
                return None
                
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
        # Improved regex to handle various sentence endings better
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If a single sentence is already too long, we might need to split by commas or spaces
            if len(sentence) > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # Sub-split long sentence
                sub_parts = re.split(r'(?<=,)\s+|\s+', sentence)
                sub_chunk = ""
                for part in sub_parts:
                    if len(sub_chunk) + len(part) + 1 <= max_length:
                        sub_chunk += part + " "
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk.strip())
                        sub_chunk = part + " "
                if sub_chunk:
                    current_chunk = sub_chunk
            elif len(current_chunk) + len(sentence) + 1 <= max_length:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
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
