import yt_dlp
import os
from pathlib import Path
from ..models.lingua_config import settings

class Downloader:
    @staticmethod
    def download_youtube(url: str, output_dir: Path, job_id: str) -> Path:
        output_template = str(output_dir / f"{job_id}_video.%(ext)s")
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        for file in output_dir.glob(f"{job_id}_video.*"):
            return file
        return None

    @staticmethod
    def download_youtube_audio(url: str, output_dir: Path, job_id: str) -> Path:
        output_template = str(output_dir / f"{job_id}_audio.%(ext)s")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        for file in output_dir.glob(f"{job_id}_audio.*"):
            return file
        return None
