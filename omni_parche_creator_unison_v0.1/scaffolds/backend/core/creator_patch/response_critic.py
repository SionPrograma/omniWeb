"""
Response critic scaffold.

Checks whether the result is useful, clear, safe, and aligned with the mission.
"""

from typing import Dict, Any


class ResponseCritic:
    def review(self, result: Dict[str, Any]) -> Dict[str, Any]:
        output = result.get("output", "")
        useful = bool(output)
        return {
            "useful": useful,
            "clarity_score": 1.0 if useful else 0.0,
            "risk_flag": False,
            "notes": "Scaffold critic result only; wire to real policy/review logic."
        }
