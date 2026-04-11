import re
from typing import Dict, Any, List, Optional
from backend.core.governance.mode_registry import OmniMode

class PublicNormalizer:
    """
    V1.0 Block 03: Governed Result Normalizer.
    Translates internal technical AI responses into product-grade public language.
    Suppresses tactical metadata and enforces persona boundaries.
    """
    
    # 1. Linguistic Translation (Internal -> Public)
    # Case-insensitive replacements
    TRANSLATIONS = {
        r"\bMisión\b": "Operación",
        r"\bMission\b": "Operation",
        r"\bForge\b": "Sistema",
        r"\bArtifact\b": "Resultado",
        r"\bArtefacto\b": "Resultado",
        r"\bTactical Overlay\b": "Detalles Visuales",
        r"\bTask ID\b": "Referencia",
        r"\bDrift\b": "Desviación",
        r"\bNominal\b": "Correcto",
        r"\bSubprocess\b": "Paso"
    }

    # 2. Key Suppression (Payload Blacklist)
    FORBIDDEN_KEYS = {
        "tactical_overlay",
        "technical_trace",
        "debug_info",
        "internal_logs",
        "mission_status",
        "execution_tree",
        "resource_locks",
        "raw_diff"
    }

    def normalize_response(self, text: str, payload: Dict[str, Any], mode: OmniMode) -> tuple[str, Dict[str, Any]]:
        """
        Main entry point for response shaping.
        Only applies transformations if the mode is PUBLIC.
        """
        if mode != OmniMode.PUBLIC:
            return text, payload

        # 1. Text Normalization
        normalized_text = self._clean_text(text)
        
        # 2. Payload Sanitization
        sanitized_payload = self._clean_payload(payload)
        
        return normalized_text, sanitized_payload

    def _clean_text(self, text: str) -> str:
        """Applies linguistic filters to remove creator-centric terminology."""
        if not text:
            return ""
            
        clean = text
        for pattern, replacement in self.TRANSLATIONS.items():
            clean = re.sub(pattern, replacement, clean, flags=re.IGNORECASE)
            
        # 3. Strip complex markdown blocks that are explicitly technical
        # e.g. [!CAUTION] with technical rationale
        # Only preserve if we can make it friendly. For now, keep it simple.
        
        return clean.strip()

    def _clean_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Strips technical keys from the payload to prevent leakage."""
        if not payload:
            return {}
            
        # Create a copy to avoid mutating the original reference
        clean = {}
        for k, v in payload.items():
            if k in self.FORBIDDEN_KEYS:
                continue
            
            # Recursive cleaning for nested dicts
            if isinstance(v, dict):
                clean[k] = self._clean_payload(v)
            elif isinstance(v, list):
                clean[k] = [self._clean_payload(item) if isinstance(item, dict) else item for item in v]
            else:
                clean[k] = v
                
        return clean

# Singleton
public_normalizer = PublicNormalizer()
