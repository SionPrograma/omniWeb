from typing import Dict, List, Optional

class PatternReplayEngine:
    """
    Manages musical training sessions, phrase looping, and playback modulation.
    Provides technique-specific markers for practice.
    """

    TECHNIQUES = {
        "vibrato": "〰️",
        "slide": "↗️",
        "ghost_note": "👻",
        "accent": "💥",
        "legato": "⁀",
        "staccato": "•",
        "hammer_on": "🔨",
        "pull_off": "🪝"
    }

    def __init__(self):
        self.active_loop: Optional[Tuple[float, float]] = None
        self.playback_speed: float = 1.0

    def create_training_session(self, audio_id: str, pattern: List[Dict]) -> Dict:
        """
        Initializes a training session with a specific pattern.
        """
        return {
            "session_id": f"music_{audio_id}",
            "pattern_length": len(pattern),
            "bpm": 120, # Default, can be overridden
            "layers": [
                {"name": "Original Audio", "type": "audio"},
                {"name": "Note Grid", "type": "visual"},
                {"name": "Technique Guide", "type": "overlay"}
            ]
        }

    def get_rhythmic_grid(self, pattern: List[Dict], subdivisions: int = 16) -> List[str]:
        """
        Builds a visual rhythmic grid for the phrase.
        """
        # subdivision grid (e.g., 16 columns)
        grid = ["_"] * subdivisions
        for note in pattern:
            pos = int((note["time_ms"] / 2000) * subdivisions) % subdivisions
            char = "N"
            if note.get("technique"):
                char = self.TECHNIQUES.get(note["technique"], "N")
            grid[pos] = char
            
        return grid

    def set_loop(self, start_ms: float, end_ms: float):
        """Sets the active loop boundaries."""
        self.active_loop = (start_ms, end_ms)

    def set_speed(self, speed: float):
        """Sets playback speed (0.25, 0.5, 0.75, 1.0)."""
        valid_speeds = [0.25, 0.5, 0.75, 1.0]
        if speed in valid_speeds:
            self.playback_speed = speed

    def get_technique_markers(self, note_idx: int, metadata: Dict) -> List[str]:
        """
        Returns visual markers for techniques detected in a specific note.
        """
        active_markers = []
        for tech, symbol in self.TECHNIQUES.items():
            if metadata.get(tech):
                active_markers.append(symbol)
        return active_markers

    def analyze_accuracy(self, original: List[Dict], detected: List[Dict]) -> Dict:
        """
        Compares user performance against the pattern to provide feedback.
        """
        if not detected: return {"accuracy": 0, "feedback": "Keep trying!"}
        
        # Simple comparison of pitch and timing
        pitch_hits = 0
        timing_hits = 0
        
        for d in detected:
            matches = [o for o in original if o["note"] == d["note"]]
            if matches:
                pitch_hits += 1
                # Check timing (e.g., within 50ms)
                if any(abs(o["time_ms"] - d["time_ms"]) < 50 for o in matches):
                    timing_hits += 1
                    
        accuracy = (pitch_hits + timing_hits) / (len(original) * 2)
        
        return {
            "accuracy_score": round(accuracy * 100, 1),
            "feedback": "Perfect timing!" if accuracy > 0.9 else "Focus on the groove",
            "stats": {
                "pitch_score": pitch_hits / len(original),
                "timing_score": timing_hits / len(original)
            }
        }
