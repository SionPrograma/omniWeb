import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AgentIconRenderer:
    """Generates visual properties and SVG metadata for AI agents."""
    
    def get_icon_style(self, agent_name: str, status: str) -> Dict[str, Any]:
        """Returns CSS and icon properties for a specific agent."""
        # Mapping names to gradients
        themes = {
            "DevAI": "linear-gradient(135deg, #a855f7, #3b82f6)",
            "Scout": "linear-gradient(135deg, #10b981, #3b82f6)",
            "Muse": "linear-gradient(135deg, #f43f5e, #fb923c)"
        }
        
        return {
            "background": themes.get(agent_name, "var(--accent-color)"),
            "animation": "pulse" if status == "speaking" else "none",
            "scale": 1.1 if status == "thinking" else 1.0
        }

agent_icon_renderer = AgentIconRenderer()
