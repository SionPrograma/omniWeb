from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from .evidence_engine import EvidenceItem, EvidenceBundle

class DiagnosisCategory(str, Enum):
    NOMINAL = "nominal"
    LATENCY_SPIKE = "latency_spike"
    MEMORY_SATURATION = "memory_saturation"
    CHIP_ERROR = "chip_error"
    SYSTEM_WARNING = "system_warning"
    RESOURCE_CONTENTION = "resource_contention"
    CONFLICT = "conflict"
    INSUFFICIENT_DATA = "insufficient_data"

@dataclass
class StructuredDiagnosis:
    """
    Mathematical, deterministic diagnosis of the system runtime.
    Replaces the old 'TechnicalClaim' narrative string wrapper.
    """
    diagnosis_type: str
    confidence_score: float
    detected_anomalies: List[Dict[str, Any]] = field(default_factory=list)
    supporting_evidence: List[EvidenceItem] = field(default_factory=list)
    clarification_needed: bool = False
    constraints: List[str] = field(default_factory=list)
    recommended_mode: str = "conversational"
    hypothesis_id: Optional[str] = None
    
    # Legacy wrapper for backwards compatibility with reflective_deliberation until next phase
    @property
    def claim(self) -> str:
        return f"[{self.diagnosis_type.upper()}] Conf:{self.confidence_score} | Anomalies:{len(self.detected_anomalies)}"
        
    @property
    def confidence(self) -> float:
        return self.confidence_score
        
    @property
    def is_insufficient(self) -> bool:
        return self.diagnosis_type == DiagnosisCategory.INSUFFICIENT_DATA.value
        
    @property
    def conflict_detected(self) -> bool:
        return self.diagnosis_type == DiagnosisCategory.CONFLICT.value
    
    @property
    def limitations(self) -> List[str]:
        return self.constraints

# Alias safely for backward compatibility in imports
TechnicalClaim = StructuredDiagnosis

class RuntimeTruthEvaluator:
    """
    Evaluates evidence mathematically and builds grounded technical diagnosis.
    Prevents the AI from hallucinating causes by enforcing strict telemetry thresholds.
    """
    def evaluate(self, bundle: EvidenceBundle, request_msg: Optional[str] = None) -> StructuredDiagnosis:
        # 1. Parse Input Context
        user_symptom = False
        if request_msg:
            low_msg = request_msg.lower()
            if any(w in low_msg for w in ["falla", "no carga", "no se ve", "problema", "bug", "roto", "anda mal"]):
                user_symptom = True

        if not bundle.has_sufficient_evidence:
            return StructuredDiagnosis(
                diagnosis_type=DiagnosisCategory.INSUFFICIENT_DATA.value,
                confidence_score=0.2 if user_symptom else 0.1,
                clarification_needed=True,
                constraints=[bundle.uncertainty_reason or "No supporting metrics found."],
                recommended_mode="clarification"
            )

        # 2. Hard Mathematical Thresholds extraction
        anomalies = []
        latencies = []
        memory_issues = []
        
        has_overall_warning = False
        
        for i in bundle.items:
            # Detect Latency Spikes (Threshold > 300ms)
            if "latency" in i.key and isinstance(i.value, (int, float)):
                if i.value > 300:
                    latencies.append(i)
                    anomalies.append({"type": "latency", "source": i.key, "value": i.value})
            
            # Detect Memory Saturation (Threshold > 85%)
            if "memory" in i.key and isinstance(i.value, (int, float)):
                if i.value > 85:
                    memory_issues.append(i)
                    anomalies.append({"type": "memory", "source": i.key, "value": i.value})
            
            # Detect Generic Text Errors/Warnings
            if isinstance(i.value, str):
                val_lower = i.value.lower()
                if "warning" in val_lower or "error" in val_lower or "offline" in val_lower or "failed" in val_lower:
                    if i.key == "health" and i.source == "system_state":
                        has_overall_warning = True
                    else:
                        anomalies.append({"type": "status_error", "source": i.key, "value": i.value})

        # 3. Decision Matrix & Scoring
        has_specific_culprit = len(anomalies) > 0
        
        # Conflict state: Master warning but no telemetry supports it
        if has_overall_warning and not has_specific_culprit:
            return StructuredDiagnosis(
                diagnosis_type=DiagnosisCategory.CONFLICT.value,
                confidence_score=0.4,
                clarification_needed=True,
                constraints=["System health reports warning but no sub-module exhibits anomalous metrics."],
                recommended_mode="reflective_analysis"
            )
            
        # Nominal State
        if not has_specific_culprit:
             return StructuredDiagnosis(
                diagnosis_type=DiagnosisCategory.NOMINAL.value,
                confidence_score=0.9 if not user_symptom else 0.5,
                clarification_needed=user_symptom, # If user complains but system is perfect = needs clarification
                recommended_mode="conversational" if not user_symptom else "clarification"
             )
             
        # Active Anomaly State
        diag_type = DiagnosisCategory.SYSTEM_WARNING.value
        confidence = 0.6
        rec_mode = "reflective_analysis"
        
        supporting_evidence = []
        
        if latencies and memory_issues:
            diag_type = DiagnosisCategory.RESOURCE_CONTENTION.value
            confidence = 0.95
            supporting_evidence.extend(latencies + memory_issues)
            rec_mode = "remediation"
        elif latencies:
            diag_type = DiagnosisCategory.LATENCY_SPIKE.value
            confidence = 0.85
            supporting_evidence.extend(latencies)
            rec_mode = "remediation"
        elif memory_issues:
            diag_type = DiagnosisCategory.MEMORY_SATURATION.value
            confidence = 0.90
            supporting_evidence.extend(memory_issues)
            rec_mode = "remediation"
        else:
            diag_type = DiagnosisCategory.CHIP_ERROR.value
            confidence = 0.80
            # Pull any item that matches the anomalies
            for a in anomalies:
                match = next((i for i in bundle.items if i.key == a["source"]), None)
                if match: supporting_evidence.append(match)

        # Build ultimate payload
        diag_obj = StructuredDiagnosis(
            diagnosis_type=diag_type,
            confidence_score=confidence,
            detected_anomalies=anomalies,
            supporting_evidence=supporting_evidence,
            clarification_needed=False,
            constraints=["Targeted repair required"],
            recommended_mode=rec_mode
        )

        # --- STAGE 11: Register Hypothesis in Cognitive Core ---
        try:
            from ..cognition.cognitive_core import cognitive_core
            desc = f"Local Deterministic Diagnosis: {diag_obj.diagnosis_type}"
            h_id = cognitive_core.register_hypothesis(
                description=desc,
                supporting_evidence=[f"{i.source}.{i.key}={i.value}" for i in diag_obj.supporting_evidence],
                confidence=diag_obj.confidence_score,
                status="active"
            )
            diag_obj.hypothesis_id = h_id
        except Exception as e:
            pass

        return diag_obj

runtime_truth = RuntimeTruthEvaluator()

