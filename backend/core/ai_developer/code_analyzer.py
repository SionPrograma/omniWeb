import os
import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """
    Inspects existing chips to understand their structure and components.
    """
    def analyze_chip(self, chip_slug: str) -> Dict[str, Any]:
        """
        Scans a chip directory and identifies its core files.
        """
        # Adapt chip_slug if it's format chip-name
        folder_name = f"chip-{chip_slug}" if not chip_slug.startswith("chip-") else chip_slug
        chip_path = os.path.join("chips", folder_name)

        if not os.path.exists(chip_path):
            return {"status": "error", "message": f"Chip {folder_name} not found."}
            
        analysis = {
            "slug": chip_slug,
            "path": chip_path,
            "files": [],
            "frontend": [],
            "backend": [],
            "migrations": [],
            "permissions": [],
            "routes_detected": [],
            "config": None
        }
        
        for root, dirs, files in os.walk(chip_path):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), chip_path)
                analysis["files"].append(rel_path)
                
                # Identify configuration
                if file == "chip.json":
                    analysis["config"] = rel_path
                    
                # Identify Frontend components
                elif "frontend" in root or file.endswith((".html", ".css", ".js", ".png", ".jpg")):
                    analysis["frontend"].append(rel_path)
                
                # Identify Backend / Core logic
                elif "core" in root or file.endswith(".py"):
                    analysis["backend"].append(rel_path)
                    
                    if "migrations" in root:
                        analysis["migrations"].append(rel_path)
                    
                    if file == "permissions.py":
                         analysis["permissions"].append(rel_path)
                    
                    if file == "router.py":
                        # Attempt to basic-scan routes
                        try:
                            full_path = os.path.join(root, file)
                            with open(full_path, "r") as f:
                                content = f.read()
                                # Very simple route detection for the summary
                                import re
                                routes = re.findall(r"@router\.(get|post|put|delete)\(\"([^\"]+)\"", content)
                                if routes:
                                    analysis["routes_detected"].extend([f"{m[0].upper()} {m[1]}" for m in routes])
                        except Exception as e:
                            logger.error(f"Error scanning routes in {file}: {e}")
                            
        return analysis

code_analyzer = CodeAnalyzer()
