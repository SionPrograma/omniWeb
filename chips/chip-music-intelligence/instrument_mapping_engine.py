from typing import Dict, List, Tuple

class InstrumentMappingEngine:
    """
    Translates musical notes into physical instrument coordinates.
    Supports Bass, Guitar, Piano, and Drums.
    """

    # Fretboard Tuning (Standard)
    TUNINGS = {
        "guitar": ["E2", "A2", "D3", "G3", "B3", "E4"],
        "bass": ["E1", "A1", "D2", "G2"]
    }

    @staticmethod
    def note_to_midi(note_name: str) -> int:
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        name = note_name[:-1]
        octave = int(note_name[-1])
        return 12 * (octave + 1) + notes.index(name)

    def get_fretboard_positions(self, instrument: str, note: str) -> List[Dict]:
        """
        Finds all possible string/fret combinations for a given note.
        """
        if instrument not in self.TUNINGS:
            return []
            
        target_midi = self.note_to_midi(note)
        positions = []
        
        for string_idx, start_note in enumerate(self.TUNINGS[instrument]):
            start_midi = self.note_to_midi(start_note)
            fret = target_midi - start_midi
            
            if 0 <= fret <= 24: # Limit to 24 frets
                positions.append({
                    "string": string_idx + 1,
                    "fret": fret,
                    "is_open": fret == 0,
                    "hand_position": "Low" if fret < 5 else "High"
                })
        
        return positions

    def map_to_piano(self, note: str) -> Dict:
        """
        Maps a note to a piano key index (0-87).
        """
        midi = self.note_to_midi(note)
        key_idx = midi - 21 # MIDI 21 is A0
        
        if 0 <= key_idx <= 87:
            return {
                "key_index": key_idx,
                "color": "black" if "#" in note else "white",
                "hand_suggested": "right" if key_idx > 40 else "left"
            }
        return {"error": "Out of range"}

    def map_to_drums(self, trigger_type: str) -> Dict:
        """
        Maps percussive inputs to drum zones.
        """
        zones = {
            "low": {"component": "Kick Drum", "zone": "Center"},
            "mid": {"component": "Snare", "zone": "Rimshot" if "accent" in trigger_type else "Head"},
            "high": {"component": "Hi-Hat", "zone": "Edge" if "open" in trigger_type else "Top"},
            "crash": {"component": "Crash Cymbal", "zone": "Edge"}
        }
        return zones.get(trigger_type, {"component": "Percussion", "zone": "Unknown"})

    def generate_fingering_guidance(self, sequence: List[str], instrument: str) -> List[Dict]:
        """
        Suggests optimal finger placement for a sequence of notes.
        """
        # Simplistic logic: choose the position closest to previous position
        guidance = []
        last_fret = 0
        
        for note in sequence:
            options = self.get_fretboard_positions(instrument, note)
            if not options: continue
            
            # Pick option with minimum fret jump
            best_opt = min(options, key=lambda x: abs(x["fret"] - last_fret))
            guidance.append({
                "note": note,
                "position": best_opt,
                "finger": self._suggest_finger(best_opt["fret"])
            })
            last_fret = best_opt["fret"]
            
        return guidance

    def _suggest_finger(self, fret: int) -> str:
        # Simple modulo-based finger suggestion for basic training
        if fret == 0: return "None (Open)"
        f = (fret % 4) + 1
        return f"Finger {f}"
