import math
from typing import Dict, List, Optional, Tuple

class PrecisionPitchEngine:
    """
    Advanced Engine for musical pitch detection and analysis.
    Target resolution: ±1 cent.
    """
    
    # Standard frequencies for notes in Octave 4 (A4 = 440Hz)
    NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    A4_FREQ = 440.0

    @staticmethod
    def frequency_to_note(frequency: float) -> Dict:
        """
        Converts a frequency (Hz) to a musical note with precision analysis.
        """
        if frequency <= 0:
            return {"error": "Invalid frequency"}

        # n = 12 * log2(fn / f0)
        n = 12 * math.log2(frequency / PrecisionPitchEngine.A4_FREQ)
        
        # Rounded semi-tones from A4
        n_rounded = round(n)
        
        # Cents deviation
        deviation = (n - n_rounded) * 100
        
        # Absolute note index (A4 is 57 semi-tones from C0 in MIDI terminology, 
        # but let's calculate relative to C0 directly)
        # MIDI note 69 is A4.
        midi_note = n_rounded + 69
        
        octave = (midi_note // 12) - 1
        note_name = PrecisionPitchEngine.NOTES[midi_note % 12]
        
        return {
            "frequency": round(frequency, 2),
            "note": note_name,
            "octave": int(octave),
            "midi": int(midi_note),
            "deviation_cents": round(deviation, 2),
            "is_in_tune": abs(deviation) < 5,
            "scientific_notation": f"{note_name}{octave}"
        }

    @staticmethod
    def detect_vibrato(frequency_history: List[float], sample_rate: float) -> Dict:
        """
        Analyzes pitch drift over time to detect vibrato patterns.
        """
        if len(frequency_history) < 10:
            return {"status": "insufficient_data"}

        # Calculate cents for each sample relative to the first one or average
        avg_freq = sum(frequency_history) / len(frequency_history)
        cents_history = [1200 * math.log2(f / avg_freq) for f in frequency_history]
        
        max_cents = max(cents_history)
        min_cents = min(cents_history)
        extent = max_cents - min_cents
        
        # Simple zero-crossing or peak detection for rate would go here
        # Mocking rate for now without full DSP library
        is_vibrato = extent > 10 and extent < 150 # Vibrato is usually between 10-100 cents
        
        return {
            "is_vibrato": is_vibrato,
            "extent_cents": round(extent, 2),
            "rate_hz": 6.0 if is_vibrato else 0.0, # Average human vibrato rate
            "drift_cents": round(sum(cents_history) / len(cents_history), 2)
        }

    @staticmethod
    def analyze_harmonics(fundamental: float, partials: List[float]) -> Dict:
        """
        Detects harmonic structure and timber characteristics.
        """
        harmonics = []
        for p in partials:
            if p <= fundamental: continue
            ratio = p / fundamental
            nearest_harmonic = round(ratio)
            error = abs(ratio - nearest_harmonic)
            
            if error < 0.1: # Threshold for harmonic relation
                harmonics.append({
                    "number": nearest_harmonic,
                    "frequency": p,
                    "perfection": round(1.0 - error, 3)
                })
        
        return {
            "fundamental": fundamental,
            "harmonic_count": len(harmonics),
            "series": harmonics,
            "is_rich": len(harmonics) > 5
        }
