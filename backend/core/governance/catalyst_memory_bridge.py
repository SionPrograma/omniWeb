import json
import logging
import re
from typing import List, Dict, Any, Optional
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class CatalystMemoryBridge:
    """
    OMNIWEB — BLOQUE: OMNI_CATALYST_MEMORY_BRIDGE_V0.2.
    Safe read-only technical context provider for catalysts.
    """
    
    def __init__(self):
        self.max_context_fragments = 3
        # Strict allowed technical categories
        self.allowed_categories = ["TACTIC", "PATTERN", "TECHNICAL_SPEC"]
        # Explicitly forbidden string patterns in any retrieved context
        self.forbidden_patterns = [
            r"POLICY-", r"GOV-", r"CREATOR-", r"SECRET-", 
            r"PASS-", r"KEY-", r"API_KEY"
        ]

    def _is_bridge_enabled(self) -> bool:
        with db_manager.get_connection() as conn:
            enabled = conn.execute("SELECT current_value FROM governance_engine_parameters WHERE param_key = 'CATALYST_MEMORY_BRIDGE_ENABLED'").fetchone()
            return enabled and enabled["current_value"] == 'true'

    def get_technical_context_pack(self, tactic_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves a small pack of related technical wisdom nodes if the bridge is enabled.
        """
        if not self._is_bridge_enabled():
            return []

        context_pack = []
        try:
            with db_manager.get_connection() as conn:
                # V0.2: Get 2-3 technical tactics related to the current domain or ID
                # If tactic_id is provided, look for similar nodes. 
                # Else return a generic healthy technical summary.
                
                query = """
                    SELECT node_id, title, summary, status_band 
                    FROM governance_wisdom_atlas_nodes 
                    WHERE node_type IN ('TACTIC', 'PATTERN')
                      AND status_band IN ('STRONG_REUSABLE_BASELINE', 'CROSS_CONTEXT_CONFIRMED_TACTIC')
                    LIMIT ?
                """
                nodes = conn.execute(query, (self.max_context_fragments,)).fetchall()
                
                for n in nodes:
                    fragment = {
                        "node_id": n["node_id"],
                        "title": n["title"],
                        "summary": n["summary"]
                    }
                    if self._safe_filter(fragment):
                        context_pack.append(fragment)
                        
        except Exception as e:
            logger.error(f"Memory Bridge Retrieval failed: {e}")
            
        return context_pack

    def _safe_filter(self, fragment: Dict[str, Any]) -> bool:
        """
        Security check: ensures no sensitive patterns are in the retrieved fragment.
        """
        content = json.dumps(fragment).upper()
        for pattern in self.forbidden_patterns:
            if re.search(pattern, content):
                logger.warning(f"Memory Bridge: Filtered fragment due to forbidden pattern {pattern}")
                return False
        return True

    def scrub_fragment(self, fragment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove any remaining internal IDs or absolute paths.
        """
        scrubbed = {}
        for k, v in fragment.items():
            if isinstance(v, str):
                # Mandatory scrubbing for IDs and Paths
                # Mandatory scrubbing for IDs and Paths (Refined V0.4)
                v = re.sub(r"[a-f0-9]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "[PROTECTED_UUID]", v, flags=re.I)
                v = re.sub(r"(OMNI|LEDG|SYNC|DRAFT|CAT|MNODE|WNODE|ID|B)-(?=[A-Z0-9]{6,})[A-Z0-9]+", "[PROTECTED_SYSTEM_ID]", v, flags=re.I)
                v = re.sub(r"[a-zA-Z]:\\[^\"'\s]+", "[PROTECTED_PATH]", v)
                scrubbed[k] = v
            else:
                scrubbed[k] = v
        return scrubbed

catalyst_memory_bridge = CatalystMemoryBridge()
