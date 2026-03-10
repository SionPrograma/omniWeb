from .downloader import Downloader
from .audio_converter import AudioConverter
from .transcriber import Transcriber
from .translator import Translator
from .tts_generator import TTSGenerator
from .audio_merger import AudioMerger
from .subtitle_generator import SubtitleGenerator
from .job_manager import job_manager
from ..models.lingua_config import settings
from .file_utils import get_job_dir, clean_temp_files
import os
import shutil
from pathlib import Path
import json
import gc

class ProcessingService:
    def __init__(self):
        # We don't initialize large AI objects here to delay load to when exactly needed
        pass

    async def run_pipeline(self, job_id: str, url: str = None, file_path: Path = None, target_lang: str = "es"):
        job_status = "processing"
        
        # Ensure heavy objects are only loaded when needed within the pipeline scope
        transcriber = None
        translator = None
        tts = None
        
        try:
            # 0. Ensure Directories Exist
            settings.create_directories()
            
            # 1. Acquire Source
            job_manager.update_job(job_id, "preparation", 5.0, "Initializing workspace...", status=job_status)
            job_dir = get_job_dir(settings.TEMP_DIR, job_id)
            
            if url:
                job_manager.update_job(job_id, "downloading", 10.0, "Downloading from YouTube...", status=job_status)
                video_path = Downloader.download_youtube(url, job_dir, job_id)
            else:
                video_path = file_path
            
            if not video_path or not video_path.exists():
                raise Exception("Failed to acquire video source. Check URL or file format.")

            # 2. Extract Audio
            job_manager.update_job(job_id, "audio_extraction", 20.0, "Extracting audio for analysis...", stage_completed="downloading", status=job_status)
            original_audio = AudioConverter.extract_audio(video_path, job_id)

            # Force garbage collection early
            gc.collect()

            # 3. Transcribe
            job_manager.update_job(job_id, "transcribing", 40.0, f"Transcribing with Whisper ({settings.WHISPER_MODEL})...", stage_completed="audio_extraction", status=job_status)
            transcriber = Transcriber()
            transcript_data = transcriber.transcribe(original_audio)
            segments = transcript_data.get('segments', [])
            
            # Explicitly free the Whisper model after transcription
            transcriber._cleanup_memory()
            del transcriber
            gc.collect()

            # 4. Translate per segment (for sync)
            job_manager.update_job(job_id, "translating", 60.0, f"Translating segments to {target_lang}...", stage_completed="transcribing", status=job_status)
            
            translated_segments = []
            full_translated_text = []
            translation_success = True
            num_segments = len(segments)
            translator = Translator()
            
            try:
                for i, segment in enumerate(segments):
                    sub_percent = 60.0 + ((i + 1) / num_segments) * 10.0 if num_segments > 0 else 70.0
                    job_manager.update_job(job_id, "translating", round(float(sub_percent), 1), f"Translating segment {i+1}/{num_segments}...", status=job_status)
                    
                    translated_text = translator.translate(segment['text'], target_lang)
                    segment['translated_text'] = translated_text
                    translated_segments.append(segment)
                    full_translated_text.append(translated_text)
                    
            except Exception as trans_e:
                print(f"Translation step failed unexpectedly: {trans_e}")
                job_status = "partial_success"
                job_manager.update_job(job_id, "translating", 70.0, f"Translation failed: {trans_e}. Using original text.", status=job_status)
                translation_success = False
                # Fallback to original transcript
                for segment in segments:
                    if 'translated_text' not in segment:
                        segment['translated_text'] = segment['text']
                        translated_segments.append(segment)
                        full_translated_text.append(segment['text'])

            # Free translator
            translator = None
            gc.collect()

            # 4.1. Save full transcript data and translation unconditionally
            try:
                with open(settings.TRANSCRIPT_OUTPUT / f"{job_id}.json", "w", encoding="utf-8") as f:
                    json.dump(transcript_data, f, indent=2)

                with open(settings.TRANSLATION_OUTPUT / f"{job_id}.txt", "w", encoding="utf-8") as f:
                    f.write(" ".join(full_translated_text))
            except Exception as save_e:
                print(f"Failed to save transcript/translation artifact files: {save_e}")
                
            # Explicitly free transcript metadata
            del transcript_data
            gc.collect()
            
            # 5. Generate Dubbing (TTS)
            tts_success = False
            dub_audio_path = None
            if settings.TTS_ENABLED:
                try:
                    job_manager.update_job(job_id, "synthesizing", 80.0, f"Generating AI voice (CPU-friendly: {settings.CPU_FRIENDLY_MODE})...", stage_completed="translating", status=job_status)
                    tts = TTSGenerator()
                    dub_audio_path = settings.AUDIO_OUTPUT / f"{job_id}_dub.wav"
                    
                    # Generate speech (will handle internal chunking and cleanup)
                    tts_result = tts.generate(
                        text=" ".join(full_translated_text), 
                        output_path=dub_audio_path, 
                        speaker_wav=original_audio, 
                        language=target_lang
                    )
                    if tts_result:
                        tts_success = True
                except Exception as tts_e:
                    print(f"TTS Generation failed: {tts_e}")
                    job_status = "partial_success"
                    job_manager.update_job(job_id, "synthesizing", 80.0, f"TTS failed or stalled: {tts_e}.", status=job_status)
                finally:
                    # Release TTS object and text variables as soon as no longer needed
                    tts = None
                    del full_translated_text
                    gc.collect()
            else:
                job_manager.update_job(job_id, "synthesizing", 80.0, "TTS bypassed (config disabled).", stage_completed="translating", status=job_status)
                # Cleanup text variable even if TTS is skipped
                del full_translated_text
                gc.collect()

            # 6. Generate Subtitles
            job_manager.update_job(job_id, "subtitles", 90.0, "Creating synchronized subtitles...", stage_completed="synthesizing" if tts_success else "translating", status=job_status)
            try:
                SubtitleGenerator.create_srt(segments, settings.SUBTITLE_OUTPUT / f"{job_id}.srt", use_translated=translation_success)
            except Exception as sub_e:
                print(f"Subtitle Generation failed: {sub_e}")
                job_status = "partial_success"
                job_manager.update_job(job_id, "subtitles", 90.0, f"Subtitles failed: {sub_e}.", status=job_status)
            finally:
                # Release segment variables
                del segments
                del translated_segments
                gc.collect()

            # 7. Merge into final video
            if tts_success and dub_audio_path and dub_audio_path.exists() and video_path.suffix != ".mp3":
                try:
                    job_manager.update_job(job_id, "merging", 95.0, "Merging audio and video tracks...", stage_completed="subtitles", status=job_status)
                    final_video_name = f"{job_id}_final.mp4"
                    final_video_path = settings.MERGED_OUTPUT / final_video_name
                    AudioMerger.merge_audio_with_original(str(video_path), str(dub_audio_path), str(final_video_path))
                    
                    # 8. Complete
                    result_url = f"/outputs/merged/{final_video_name}"
                    final_status = "completed" if job_status == "processing" else "partial_success"
                    job_manager.update_job(job_id, "complete", 100.0, "Processing complete!", result_url=result_url, stage_completed="merging", status=final_status)
                except Exception as merge_e:
                    print(f"Merging failed: {merge_e}")
                    job_status = "partial_success"
                    job_manager.update_job(job_id, "complete", 100.0, f"Merging failed. Results partially available.", stage_completed="subtitles", status=job_status)
            else:
                # 8. Complete - Partial Success
                job_status = "partial_success"
                msg = "Processing complete (TTS disabled or failed)." if not settings.TTS_ENABLED else "Processing complete (Subtitles / Transcript only)."
                job_manager.update_job(job_id, "complete", 100.0, msg, stage_completed="subtitles", status=job_status)

        except Exception as e:
            # Handle catastrophic failures
            print(f"Catastrophic pipeline failure: {e}")
            current_job = job_manager.get_job(job_id)
            current_percent = current_job["percent"] if current_job else 0.0
            job_manager.update_job(job_id, "failed", current_percent, str(e), error=str(e), status="failed")

        finally:
            # Assure final cleanup is always done
            clean_temp_files(job_id)
            gc.collect()

processing_service = ProcessingService()
