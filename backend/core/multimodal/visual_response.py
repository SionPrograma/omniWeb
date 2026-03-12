from typing import List, Dict, Any, Optional

class VisualResponseEngine:
    """
    Constructs structured visual payloads for the OmniWeb Dashboard.
    Supports charts, tables, and node diagrams.
    """
    
    @staticmethod
    def create_chart(title: str, labels: List[str], values: List[float], chart_type: str = "bar") -> Dict[str, Any]:
        return {
            "type": f"chart_{chart_type}",
            "title": title,
            "data": {
                "labels": labels,
                "values": values
            }
        }

    @staticmethod
    def create_table(title: str, headers: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
        return {
            "type": "table",
            "title": title,
            "data": {
                "headers": headers,
                "rows": rows
            }
        }

    @staticmethod
    def create_graph_view(title: str, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
        return {
            "type": "graph",
            "title": title,
            "data": {
                "nodes": nodes,
                "edges": edges
            }
        }

    @staticmethod
    def create_alert(title: str, message: str, level: str = "info") -> Dict[str, Any]:
        return {
            "type": "alert",
            "title": title,
            "data": {
                "message": message,
                "level": level
            }
        }

    @staticmethod
    def create_knowledge_map(title: str, steps: List[str]) -> Dict[str, Any]:
        return {
            "type": "knowledge_map",
            "title": title,
            "data": {
                "steps": steps
            }
        }
