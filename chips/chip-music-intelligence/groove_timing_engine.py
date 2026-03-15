from typing import Dict, List, Optional
import time

class GrooveTimingEngine:
    """
    Engine for rhythmic analysis and microtiming detection.
    Analyzes "the pocket" and groove characteristics.
    """
    
    def __init__(self, tempo_bpm: float = 120.0):
        self.tempo_bpm = tempo_bpm
        self.beat_duration = 60.0 / tempo_bpm
    
    def analyze_onsets(self, onsets_ms: List[float], velocities: List[float]) -> Dict:
        """
        Analyzes a sequence of note onsets to detect timing patterns.
        """
        if len(onsets_ms) < 4:
            return {"error": "Insufficient data"}

        deltas = [onsets_ms[i] - onsets_ms[i-1] for i in range(1, len(onsets_ms))]
        avg_delta = sum(deltas) / len(deltas)
        
        # Detected BPM from sequence
        detected_bpm = 60.0 / (avg_delta / 1000.0)
        
        # Microtiming Analysis (Deviation from perfect grid)
        deviations = []
        accents = []
        for i, onset in enumerate(onsets_ms):
            # Distance to nearest beat
            grid_pos = round(onset / (self.beat_duration * 1000.0))
            perfect_pos = grid_pos * (self.beat_duration * 1000.0)
            diff = onset - perfect_pos
            deviations.append(diff)
            
            # Accent detection based on velocity peaks
            if velocities[i] > sum(velocities)/len(velocities) * 1.5:
                accents.append(i)

        # Swing detection (Long-short ratio of subdivisions)
        swing_factor = 0.5 # Straight by default
        if len(deltas) >= 2:
            # Look for 8th note pairs
            ratios = []
            for i in range(0, len(deltas)-1, 2):
                pair_sum = deltas[i] + deltas[i+1]
                ratios.append(deltas[i] / pair_sum)
            if ratios:
                swing_factor = sum(ratios) / len(ratios)

        return {
            "bpm": round(detected_bpm, 1),
            "swing": round(swing_factor, 2),
            "microtiming_ms": [round(d, 2) for d in deviations],
            "is_pushing": sum(deviations) < -5.0, # Ahead of the beat
            "is_dragging": sum(deviations) > 5.0, # Behind the beat
            "accents": accents,
            "ghost_notes": [i for i, v in enumerate(velocities) if v < 20] # Low velocity notes
        }

    @staticmethod
    def get_playback_modifiers() -> Dict[str, float]:
        """
        Returns supported pattern replay speeds.
        """
        return {
            "full_speed": 1.0,
            "relaxed": 0.75,
            "training": 0.5,
            "precision": 0.25
        }

    def generate_timeline_visualization(self, duration_sec: float, events: List[Dict]) -> List[str]:
        """
        Generates a text-based ASCII timeline for the groove.
        """
        width = 40
        timeline = ["-"] * width
        ms_per_pixel = (duration_sec * 1000) / width
        
        for event in events:
            pixel = int(event["ms"] / ms_per_pixel)
            if 0 <= pixel < width:
                char = "|" 
                if event.get("accent"): char = "X"
                if event.get("ghost"): char = "."
                timeline[pixel] = char
                
        return ["".join(timeline)]
