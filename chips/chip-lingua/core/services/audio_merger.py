import subprocess
from pathlib import Path

class AudioMerger:
    @staticmethod
    def merge_audio_with_original(original_video: str, new_audio: str, output_path: str):
        """Replaces original audio with new audio in a video file using ffmpeg."""
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
        subprocess.run(command, check=True)
        return output_path

    @staticmethod
    def combine_audio_segments(segments_paths: list, output_path: str, job_id: str):
        """Concatenates multiple audio segments into one."""
        concat_file = Path(output_path).parent / f"concat_{job_id}.txt"
        with open(concat_file, 'w') as f:
            for p in segments_paths:
                # Use absolute paths and escape single quotes for ffmpeg
                abs_p = str(Path(p).absolute()).replace("'", "'\\''")
                f.write(f"file '{abs_p}'\n")
        
        try:
            command = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_file), '-c', 'copy', output_path]
            subprocess.run(command, check=True, capture_output=True)
        finally:
            if concat_file.exists():
                concat_file.unlink()
        return output_path
