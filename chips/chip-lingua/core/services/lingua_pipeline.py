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
        import psutil
        process = psutil.Process(os.getpid())
        
        def log_mem(step):
            mem_mb = process.memory_info().rss / (1024 * 1024)
            print(f"[MEM] {step}: {mem_mb:.2f} MB")

        # Ensure heavy objects are only loaded when needed within the pipeline scope
        transcriber = None
        translator = None
        tts = None
        
        # Keep track of intermediate files for cleanup
        intermediate_files = []
        
        try:
            log_mem("Start")
            # 0. Ensure Directories Exist
            settings.create_directories()
            
            # 1. Acquire Source
            job_manager.update_job(job_id, "preparation", 5.0, "Initializing workspace...", status=job_status)
            job_dir = get_job_dir(settings.TEMP_DIR, job_id)
            
            if url:
                job_manager.update_job(job_id, "downloading", 10.0, "Downloading content...", status=job_status)
                try:
                    video_path = Downloader.download_youtube(url, job_dir, job_id)
                except Exception as de:
                    raise Exception(f"Download failed: {str(de)}")
            else:
                video_path = file_path
            
            if not video_path or not video_path.exists():
                raise Exception("Failed to acquire source. Check URL or file path.")

            intermediate_files.append(video_path)
            log_mem("File Acquired")

            # 2. Extract Audio
            job_manager.update_job(job_id, "audio_extraction", 20.0, "Extracting audio...", stage_completed="downloading", status=job_status)
            try:
                # If already a .wav, we might still want to normalize it, but if it fails, we can try to proceed
                is_wav = video_path.suffix.lower() == ".wav"
                original_audio = AudioConverter.extract_audio(video_path, job_id)
                if not original_audio or not original_audio.exists():
                     raise Exception("Audio extraction produced no output.")
                intermediate_files.append(original_audio)
            except Exception as ae:
                if is_wav:
                    print(f"[Pipeline] Extraction failed, but source is .wav. Using original: {ae}")
                    original_audio = video_path
                else:
                    raise Exception(f"Audio extraction failed: {str(ae)}")
                
            log_mem("Audio Extracted")
            gc.collect()

            # 3. Transcribe
            job_manager.update_job(job_id, "provisioning", 35.0, "Checking ML stack availability...", stage_completed="audio_extraction", status=job_status)
            try:
                transcriber = Transcriber()
                transcript_data = await transcriber.transcribe_async(original_audio)
                segments = transcript_data.get('segments', [])
                mode = transcript_data.get('metadata', {}).get('mode', 'N/A')
                
                # Report mode in status
                job_manager.update_job(job_id, "transcribing", 40.0, f"Transcribing (Engine: {mode} / {settings.WHISPER_MODEL})...", status=job_status)
                
                if not segments:
                    print(f"[Pipeline] Warning: No segments. Mode: {mode}")
                    # We continue but will have limited output
            except Exception as te:
                print(f"[Pipeline] Transcription error: {te}")
                segments = []
                transcript_data = {"text": "Transcription failed", "segments": []}
                job_status = "partial_success"
                job_manager.update_job(job_id, "transcribing", 50.0, "Transcription failed, continuing with empty transcript.", status=job_status)
            finally:
                if transcriber:
                    transcriber._cleanup_memory()
                    del transcriber
                gc.collect()
            
            log_mem("Transcription Done")

            # 4. Translate
            job_status_internal = job_status # Track if this stage failed
            job_manager.update_job(job_id, "translating", 60.0, f"Translating to {target_lang}...", stage_completed="transcribing", status=job_status)
            
            translated_segments = []
            full_translated_text = []
            translation_success = True
            num_segments = len(segments)
            
            if num_segments > 0:
                translator = Translator()
                try:
                    # Group segments into smaller batches for progress reporting
                    batch_size = 10
                    for i in range(0, num_segments, batch_size):
                        current_batch = segments[i:i + batch_size]
                        text_batch = [s.get('text', '').strip() for s in current_batch]
                        
                        sub_percent = 60.0 + (min(i + batch_size, num_segments) / num_segments) * 10.0
                        job_manager.update_job(job_id, "translating", round(float(sub_percent), 1), f"Translating segments {min(i + batch_size, num_segments)}/{num_segments}...", status=job_status)
                        
                        translated_texts = translator.translate_batch(text_batch, target_lang)
                        
                        for idx, translated_text in enumerate(translated_texts):
                            segment_idx = i + idx
                            if segment_idx < num_segments:
                                segments[segment_idx]['translated_text'] = translated_text
                                translated_segments.append(segments[segment_idx])
                                full_translated_text.append(translated_text)
                except Exception as trans_e:
                    print(f"[Pipeline] Translation error: {trans_e}")
                    job_status = "partial_success"
                    translation_success = False
                    # Fallback for remaining segments
                    for segment in segments:
                        if 'translated_text' not in segment:
                            segment['translated_text'] = segment.get('text', '')
                            translated_segments.append(segment)
                            full_translated_text.append(segment.get('text', ''))
                finally:
                    translator = None
                    gc.collect()
            
            log_mem("Translation Done")

            # 4.1. Save Artifacts
            try:
                with open(settings.TRANSCRIPT_OUTPUT / f"{job_id}.json", "w", encoding="utf-8") as f:
                    json.dump(transcript_data, f, indent=2)

                text_to_save = " ".join([t for t in full_translated_text if t])
                if text_to_save:
                    with open(settings.TRANSLATION_OUTPUT / f"{job_id}.txt", "w", encoding="utf-8") as f:
                        f.write(text_to_save)
            except Exception as save_e:
                print(f"[Pipeline] Artifact save error: {save_e}")
                
            log_mem("Artifacts Saved")

            # 5. Generate Dubbing (TTS)
            tts_success = False
            dub_audio_path = None
            if settings.TTS_ENABLED and full_translated_text:
                try:
                    job_manager.update_job(job_id, "synthesizing", 80.0, "Generating AI voice...", stage_completed="translating", status=job_status)
                    tts = TTSGenerator()
                    dub_audio_path = settings.TEMP_DIR / f"{job_id}_dub.wav"
                    
                    combined_text = " ".join([t for t in full_translated_text if t])
                    if combined_text.strip():
                        tts_result = tts.generate(
                            text=combined_text, 
                            output_path=dub_audio_path, 
                            job_id=job_id,
                            speaker_wav=original_audio, 
                            language=target_lang
                        )
                        if tts_result and tts_result.exists():
                            tts_success = True
                            intermediate_files.append(dub_audio_path)
                    else:
                        print("[Pipeline] No text for TTS.")
                except Exception as tts_e:
                    print(f"[Pipeline] TTS error: {tts_e}")
                    job_status = "partial_success"
                finally:
                    tts = None
                    gc.collect()
            
            log_mem("TTS Done")

            # 6. Generate Subtitles
            job_manager.update_job(job_id, "subtitles", 90.0, "Generating subtitles...", stage_completed="synthesizing", status=job_status)
            try:
                if segments:
                    SubtitleGenerator.create_srt(segments, settings.SUBTITLE_OUTPUT / f"{job_id}.srt", use_translated=translation_success)
            except Exception as sub_e:
                print(f"[Pipeline] Subtitle error: {sub_e}")
                job_status = "partial_success"
            
            log_mem("Subtitles Done")

            # 7. Merge
            final_video_name = None
            if tts_success and dub_audio_path and dub_audio_path.exists() and video_path.suffix != ".mp3":
                try:
                    job_manager.update_job(job_id, "merging", 95.0, "Finalizing video...", stage_completed="subtitles", status=job_status)
                    final_video_name = f"{job_id}_final.mp4"
                    final_video_path = settings.MERGED_OUTPUT / final_video_name
                    
                    AudioMerger.merge_audio_with_original(str(video_path), str(dub_audio_path), str(final_video_path))
                    
                    if final_video_path.exists():
                        shutil.copy2(dub_audio_path, settings.AUDIO_OUTPUT / f"{job_id}.wav")
                        # Proxy-aware URL generation (hardening)
                        base_url = settings.ROOT_PATH.rstrip('/')
                        result_url = f"{base_url}/outputs/merged/{final_video_name}"
                        final_status = "completed" if job_status == "processing" else "partial_success"
                        job_manager.update_job(job_id, "complete", 100.0, "Pipeline completed.", result_url=result_url, status=final_status)
                    else:
                        raise Exception("FFmpeg failed to produce output video.")
                except Exception as merge_e:
                    print(f"[Pipeline] Merge error: {merge_e}")
                    job_status = "partial_success"
                    job_manager.update_job(job_id, "complete", 100.0, f"Merge failed: {merge_e}", status=job_status)
            else:
                job_status = "partial_success"
                job_manager.update_job(job_id, "complete", 100.0, "Pipeline finished with partial results.", status=job_status)

        except Exception as e:
            print(f"[Pipeline] Catastrophic Failure: {e}")
            job_manager.update_job(job_id, "failed", 0, str(e), error=str(e), status="failed")

        finally:
            log_mem("Cleanup Start")
            clean_temp_files(job_id)
            gc.collect()
            log_mem("Pipeline Finalized")

processing_service = ProcessingService()
