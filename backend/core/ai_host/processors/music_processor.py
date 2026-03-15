from typing import Dict, List, Optional
from .base import CommandProcessor, AICommandResponse

class MusicProcessor(CommandProcessor):
    """
    AI Host Processor for Music Intelligence Domain.
    Handles YouTube practice mode and instrument analysis requests.
    """

    async def can_handle(self, message: str) -> bool:
        keywords = [
            "music", "practice", "song", "instrument", "bass", "guitar", 
            "piano", "drums", "analyze", "groove", "pitch", "note", "tempo",
            "musica", "practica", "cancion", "instrumento", "bajo", "partitura"
        ]
        return any(kw in message.lower() for kw in keywords)

    async def process(self, message: str, context: Optional[Dict] = None) -> AICommandResponse:
        msg = message.lower()
        
        # YouTube Practice Mode
        if "youtube" in msg or "cancion" in msg or "song" in msg:
            return AICommandResponse(
                intent="music_practice_media",
                status="success",
                message="Opening YouTube Practice Mode. Enhancing audio analysis for rhythmic extraction.",
                payload={
                    "mode": "media_interaction",
                    "action": "open_player",
                    "features": ["audio_stream_extract", "realtime_pitch_detection", "groove_trainer"],
                    "ui_view": "music_lab"
                }
            )

        # Analysis Requests
        if "analyze" in msg or "analiza" in msg:
            return AICommandResponse(
                intent="music_analysis",
                status="success",
                message="Starting musical analysis. Detecting pitch, harmonics, and groove timing.",
                payload={
                    "mode": "analysis",
                    "engines": ["precision_pitch", "groove_timing"],
                    "visualization": "groove_timeline"
                }
            )

        # Instrument Mapping
        if "map" in msg or "fret" in msg or "string" in msg:
            return AICommandResponse(
                intent="music_instrument_mapping",
                status="success",
                message="Activating Instrument Mapper. Mapping notes to fretboard/keyboard positions.",
                payload={"mode": "mapping", "ui_panel": "instrument_mapper"}
            )

        return AICommandResponse(
            intent="music_help",
            status="info",
            message="I can help you practice music. Try commands like 'practice this bass groove' or 'analyze this song on YouTube'.",
            payload={"available_panels": ["Sonic Map", "Groove Trainer", "Instrument Mapper"]}
        )
