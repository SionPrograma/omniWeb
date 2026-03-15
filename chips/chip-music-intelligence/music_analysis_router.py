from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from .precision_pitch_engine import PrecisionPitchEngine
from .groove_timing_engine import GrooveTimingEngine
from .instrument_mapping_engine import InstrumentMappingEngine
from .pattern_replay_engine import PatternReplayEngine

router = APIRouter(tags=["Music Intelligence"])

# Models
class FrequencyInput(BaseModel):
    frequency: float
    history: Optional[List[float]] = None

class RhythmicInput(BaseModel):
    onsets_ms: List[float]
    velocities: List[float]
    tempo_bpm: Optional[float] = 120.0

class MappingInput(BaseModel):
    note: str
    instrument: str # bass, guitar, piano

# Endpoints
@router.post("/analyze/pitch")
async def analyze_pitch(data: FrequencyInput):
    pitch_info = PrecisionPitchEngine.frequency_to_note(data.frequency)
    if data.history:
        vibrato = PrecisionPitchEngine.detect_vibrato(data.history, 44100)
        pitch_info["vibrato"] = vibrato
    return pitch_info

@router.post("/analyze/groove")
async def analyze_groove(data: RhythmicInput):
    engine = GrooveTimingEngine(data.tempo_bpm)
    return engine.analyze_onsets(data.onsets_ms, data.velocities)

@router.post("/map/instrument")
async def map_instrument(data: MappingInput):
    engine = InstrumentMappingEngine()
    if data.instrument in ["guitar", "bass"]:
        return engine.get_fretboard_positions(data.instrument, data.note)
    elif data.instrument == "piano":
        return engine.map_to_piano(data.note)
    else:
        raise HTTPException(status_code=400, detail="Unsupported instrument")

@router.get("/training/markers")
async def get_markers():
    return PatternReplayEngine.TECHNIQUES

@router.get("/status")
async def get_status():
    return {
        "domain": "Music Intelligence",
        "status": "Active",
        "engines": [
            "Precision Pitch Engine (±1 cent)",
            "Groove Timing Engine",
            "Instrument Mapping Engine",
            "Pattern Replay Trainer"
        ]
    }
