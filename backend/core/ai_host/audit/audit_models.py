from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class AuditResult:
    passed: bool
    intent_group: str
    severity: str  # low / medium / high / critical
    failure_types: List[str] = field(default_factory=list)
    suspicious_layers: List[str] = field(default_factory=list)
    suspicious_modules: List[str] = field(default_factory=list)
    explanation: str = ""
    recommended_action: str = ""
    recommended_tool: str = "no_action"  # creator_mode, antigravity, runtime_test, no_action
    confidence: float = 0.0
    cleaned_preview: Optional[str] = None
    raw_response: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "intent_group": self.intent_group,
            "severity": self.severity,
            "failure_types": self.failure_types,
            "suspicious_layers": self.suspicious_layers,
            "suspicious_modules": self.suspicious_modules,
            "explanation": self.explanation,
            "recommended_action": self.recommended_action,
            "recommended_tool": self.recommended_tool,
            "confidence": self.confidence,
            "cleaned_preview": self.cleaned_preview,
            "raw_response": self.raw_response
        }
