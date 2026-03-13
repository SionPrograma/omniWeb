import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioMerger:
    @staticmethod
    def merge_audio_with_original(original_video: str, new_audio: str, output_path: str):
        """Replaces original audio with new audio in a video file using ffmpeg."""
        if not Path(original_video).exists():
            raise FileNotFoundError(f"Original video not found: {original_video}")
        if not Path(new_audio).exists():
            raise FileNotFoundError(f"New audio not found: {new_audio}")

        command = [
            'ffmpeg', '-y',
            '-i', original_video,
            '-i', new_audio,
            '-c:v', 'copy',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            output_path
        ]
        try:
            # Add timeout to avoid hanging indefinitely
            result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)
            logger.info(f"Audio merge completed successfully: {output_path}")
            return output_path
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg merge timed out.")
            raise Exception("Video merge timed out (FFmpeg).")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg merge failed: {e.stderr}")
            raise Exception(f"Video/Audio merge failed: {e.stderr[:200]}...")

    @staticmethod
    def combine_audio_segments(segments_paths: list, output_path: str, job_id: str):
        """Concatenates multiple audio segments into one using the ffmpeg concat demuxer."""
        if not segments_paths:
            return None
            
        concat_file = Path(output_path).parent / f"concat_{job_id}.txt"
        with open(concat_file, 'w', encoding='utf-8') as f:
            for p in segments_paths:
                # Use absolute paths and escape single quotes for ffmpeg
                abs_p = str(Path(p).absolute()).replace("'", "'\\''")
                f.write(f"file '{abs_p}'\n")
        
        try:
            command = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_file), '-c', 'copy', output_path]
            subprocess.run(command, check=True, capture_output=True, text=True)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg concatenation failed: {e.stderr}")
            # Fallback: simple copy if only one segment
            if len(segments_paths) == 1:
                import shutil
                shutil.copy2(segments_paths[0], output_path)
                return output_path
            raise Exception(f"Audio concatenation failed: {e.stderr[:200]}...")
        finally:
            if concat_file.exists():
                try:
                    concat_file.unlink()
                except: pass
