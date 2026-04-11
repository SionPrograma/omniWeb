import json
import logging
import uuid
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class CatalystEngine:
    """
    OMNIWEB — BLOQUE: OMNI_CATALYST_SKILL_BRIDGE_V0.1.
    Minimum safe implementation for external-style tactical acceleration.
    """
    
    def __init__(self):
        from backend.core.config import settings
        import os
        self.whitelisted_keys = ["objective", "context_text", "tactic_id", "technical_memory_context"]
        self.policy_file = os.path.join(settings.DATA_DIR, "system", "catalyst_policy.json")
        self._load_patterns()

    def _load_patterns(self):
        """Loads scrub and policy patterns from persistent JSON store."""
        # Defaults if file missing
        self.scrub_patterns = [
            (r"[a-zA-Z]:\\[^\"'\s]+", "[PROTECTED_PATH]"),
            (r"(^|\s)\/[a-zA-Z0-9._-]+\/[a-zA-Z0-9._\/-]+", "[PROTECTED_PATH]"),
            (r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "[PROTECTED_UUID]"),
            (r"(OMNI|LEDG|SYNC|DRAFT|CAT|MNODE|WNODE|ID|B)-(?=[A-Z0-9]{6,})[A-Z0-9]+", "[PROTECTED_SYSTEM_ID]"),
            (r"static_admin_token_[a-zA-Z0-9_]+", "[PROTECTED_TOKEN]"),
        ]
        self.forbidden_regex = [
            r"eval\s*\(", r"exec\s*\(", r"__import__\s*\(", 
            r"os\s*\.\s*system", r"subprocess\s*\.\s*",
            r"getattr\s*\(", r"setattr\s*\(",
            r"sudo\s+", r"chmod\s+", r"chown\s+", r"rm\s+-rf",
            r"powershell\s+", r"cmd\.exe", r"\/bin\/bash",
            r"ignore\s+policy", r"bypass\s+governance", r"override\s+protection",
            r"escalate\s+authority", r"disable\s+audit"
        ]
        
        try:
            import os
            if os.path.exists(self.policy_file):
                with open(self.policy_file, "r") as f:
                    data = json.load(f)
                    
                    # Store as lists first, then validate
                    scrubs = data.get("scrub_patterns", [])
                    policies = data.get("forbidden_regex", [])
                    
                    valid_scrubs = []
                    for p, ph in scrubs:
                        try:
                            re.compile(p)
                            valid_scrubs.append((p, ph))
                        except Exception:
                            logger.error(f"Catalyst Policy Store: Skipping malformed scrub pattern: {p}")

                    valid_policies = []
                    for pattern in policies:
                        try:
                            re.compile(pattern)
                            valid_policies.append(pattern)
                        except Exception:
                            logger.error(f"Catalyst Policy Store: Skipping malformed policy: {pattern}")

                    self.scrub_patterns = valid_scrubs
                    self.forbidden_regex = valid_policies
                    logger.info(f"Catalyst Policy Store: Loaded {len(self.scrub_patterns)} scrub patterns and {len(self.forbidden_regex)} policy rules.")
        except Exception as e:
            logger.error(f"Catalyst Policy Store: Failed to load {self.policy_file}, using defaults. Error: {e}")

    def _is_enabled(self, feature: str = 'CATALYST_ENABLED') -> bool:
        with db_manager.get_connection() as conn:
            enabled = conn.execute(f"SELECT current_value FROM governance_engine_parameters WHERE param_key = '{feature}'").fetchone()
            frozen = conn.execute("SELECT current_value FROM governance_engine_parameters WHERE param_key = 'CATALYST_FREEZE'").fetchone()
            return enabled and enabled["current_value"] == 'true' and frozen and frozen["current_value"] == 'false'

    def _scrub_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpia el contexto de información sensible antes de salir hacia el catalizador.
        Refinement V0.4: Multi-pass regex for diverse ID/Path patterns.
        """
        pruned = {k: v for k, v in context.items() if k in self.whitelisted_keys}
        
        for k, v in pruned.items():
            if isinstance(v, str):
                for pattern, placeholder in self.scrub_patterns:
                    v = re.sub(pattern, placeholder, v, flags=re.IGNORECASE)
                pruned[k] = v
            elif isinstance(v, list):
                # OMNI_CATALYST_MEMORY_BRIDGE_V0.4 Recurse through fragments
                new_list = []
                for item in v:
                    if isinstance(item, dict):
                        new_list.append(self._scrub_context(item))
                    elif isinstance(item, str):
                        for p, ph in self.scrub_patterns:
                            item = re.sub(p, ph, item, flags=re.IGNORECASE)
                        new_list.append(item)
                    else:
                        new_list.append(item)
                pruned[k] = new_list
        return pruned

    def _policy_gate(self, output_json: str) -> (bool, Optional[str]):
        """
        Verifica si la salida del catalizador es segura y cumple el contrato.
        Retorna (is_safe, block_pattern).
        """
        for pattern in self.forbidden_regex:
            if re.search(pattern, output_json, re.IGNORECASE):
                logger.warning(f"Catalyst Policy Gate: BLOCKED by pattern: {pattern}")
                return False, pattern
        
        try:
            data = json.loads(output_json)
            # Essential protocol keys: accept mission_steps (v0.1) or steps (v0.3)
            has_steps = "mission_steps" in data or "steps" in data
            if "objective" not in data or not has_steps:
                return False, "schema_violation"
        except:
            return False, "malformed_json"
            
        return True, None

    def execute_formatting_task(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Ruta la tarea de formateo/síntesis a través del catalizador con fallback nativo.
        Evolución V0.2: Agrega puente de memoria técnica.
        Evolución V0.3: Soporta traducción de especificaciones si el contexto lo indica.
        """
        if not self._is_enabled():
            return None

        # OMNI_CATALYST_MEMORY_BRIDGE_V0.2
        from backend.core.governance.catalyst_memory_bridge import catalyst_memory_bridge
        mem_pack = catalyst_memory_bridge.get_technical_context_pack(context.get("tactic_id"))
        if mem_pack:
            context["technical_memory_context"] = [catalyst_memory_bridge.scrub_fragment(f) for f in mem_pack]

        pruned_input = self._scrub_context(context)
        
        # TRACE START
        trace_id = f"CAT-{uuid.uuid4().hex[:8].upper()}"
        self._log_trace(trace_id, "INVOKE", pruned_input)

        try:
            # OMNI_CATALYST_SPEC_TRANSLATOR_V0.3
            is_translation = self._is_enabled('CATALYST_SPEC_TRANSLATION_ENABLED')
            
            # SIMULATED VIRTUAL CATALYST (V0.3)
            raw_result = self._virtual_catalyst_call(pruned_input, translation_mode=is_translation)
            
            is_safe, block_pattern = self._policy_gate(raw_result)
            if is_safe:
                # OMNI_CATALYST_SPEC_TRANSLATOR_V0.3
                if is_translation:
                    from backend.core.governance.spec_translator import spec_translator
                    validated_data = spec_translator.validate_spec_contract(raw_result)
                    if validated_data:
                        result = spec_translator.normalize_spec(validated_data)
                    else:
                        self._log_trace(trace_id, "CONTRACT_REJECT", {"raw": raw_result, "pattern": "spec_contract_error"})
                        return None
                else:
                    result = json.loads(raw_result)
                
                self._log_trace(trace_id, "SUCCESS", result)
                result["catalyst_assisted"] = True
                result["catalyst_trace_id"] = trace_id
                return result
            else:
                self._log_trace(trace_id, "POLICY_REJECT", {"raw": raw_result, "pattern": block_pattern})
                return None
                
        except Exception as e:
            logger.error(f"Catalyst Execution Error: {e}")
            self._log_trace(trace_id, "FAIL", {"error": str(e)})
            return None

    def _virtual_catalyst_call(self, scrubbed_input: Dict[str, Any], translation_mode: bool = False) -> str:
        """
        Simula la aceleración táctica de un catalizador externo.
        Evolución V0.3: Simula la generación de pasos estructurados.
        """
        obj = scrubbed_input.get("objective", "Unknown Task")
        
        if translation_mode:
            mock_spec = {
                "objective": f"OMNI_CATALYST_SPEC: {obj}",
                "rationale": "Optimized tactical specification translated from high-level intent.",
                "steps": [
                    {"step": "Analyze Technical Precendent", "status": "PENDING"},
                    {"step": "Verify Domain Integration", "status": "PENDING"},
                    {"step": "Synthesize Code Optimization", "status": "PENDING"}
                ],
                "confidence": 0.98,
                "risk_notes": "Minimal risk of drift. Requires manual Creator approval of generated steps."
            }
        else:
            mock_spec = {
                "objective": f"OMNI_ACCELERATED: {obj}",
                "mission_steps": [
                    {"step": "Legacy Format Synthesis", "status": "PENDING"}
                ],
                "rationale": f"Optimizado vía Catalyst Skill Bridge Bridge utilizando el contexto depurado."
            }
        return json.dumps(mock_spec)

    def _log_trace(self, trace_id: str, event_type: str, data: Any):
        with db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO governance_decision_ledger (
                    ledger_id, decision_type, target_ref_type, target_id, rationale, evidence_refs
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f"LEDG-{uuid.uuid4().hex[:8].upper()}",
                f"CATALYST_{event_type}",
                'CATALYST_TRACE',
                trace_id,
                f"Catalyst Event: {event_type}",
                json.dumps(data)
            ))
            conn.commit()

catalyst_engine = CatalystEngine()
