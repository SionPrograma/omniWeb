from pathlib import Path
import datetime

class SubtitleGenerator:
    @staticmethod
    def format_timestamp(seconds: float) -> str:
        td = datetime.timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((td.total_seconds() - total_seconds) * 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    @classmethod
    def create_srt(cls, segments: list, output_path: Path, use_translated: bool = True):
        """
        Creates an SRT file. 
        'segments' should be a list of dicts with 'start', 'end', and 'text'.
        """
        with open(output_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, 1):
                start = cls.format_timestamp(segment['start'])
                end = cls.format_timestamp(segment['end'])
                text = segment.get('translated_text' if use_translated and 'translated_text' in segment else 'text', '').strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
        return output_path
