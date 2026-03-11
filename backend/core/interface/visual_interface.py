import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class VisualInterface:
    """
    Visual Response System for structured AI output.
    Prepares AI Host for premium visual feedback like charts, panels, etc.
    """
    def create_visual_payload(self, type: str, data: Any, title: str = "") -> Dict[str, Any]:
        """
        Structures data into a format that the frontend dashboard can render as a widget.
        """
        payload = {
            "type": type, # 'chart-bar', 'chart-line', 'panel-stat', 'interactive-widget'
            "title": title,
            "data": data,
            "timestamp": "ISO_NOW" # Placeholder
        }
        logger.info(f"Generated visual response: {type} - {title}")
        return payload

    def generate_chart(self, labels: List[str], values: List[float], chart_type: str = "bar") -> Dict[str, Any]:
        """
        Specialized helper for data visualization.
        """
        return self.create_visual_payload(
            f"chart-{chart_type}",
            {"labels": labels, "values": values},
            "System Data Visualization"
        )

visual_interface = VisualInterface()
