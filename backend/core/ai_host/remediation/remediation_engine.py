from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from ..learning.adaptive_learning import adaptive_learning
from ..cognition.cognitive_core import cognitive_core

class RemediationOption(BaseModel):
    name: str
    description: str
    risk: str
    confidence: float

class RemediationProposal(BaseModel):
    observation: str
    likely_causes: List[str]
    solution_options: List[RemediationOption]
    recommended_solution: str
    implementation_plan: List[str]
    confidence_level: float

class RemediationEngine:
    """
    Remediation Intelligence Engine for OmniWeb.
    Translates detected system issues into structured solution proposals.
    Integrates with Engineering Memory (Adaptive Learning) patterns.
    """
    
    def __init__(self):
        self.default_confidence = 0.5

    async def analyze_and_propose(self, context: Any) -> Optional[RemediationProposal]:
        """
        Main entry point for remediation analysis.
        Triggers when system anomalies or specific user requests are detected.
        """
        # 1. IDENTIFY ANOMALIES
        anomalies = self._detect_anomalies(context)
        
        # If no specific anomalies but user requested a fix/proposal, use current topic
        if not anomalies and context.user_intent in ["creator_plan", "diagnostic"]:
            anomalies = [{"type": "general", "key": context.recent_topic or "System"}]

        if not anomalies:
            return None

        # 2. GENERATE STRUCTURED PROPOSAL
        observation = self._craft_observation(anomalies, context)
        causes = self._rank_causes(anomalies, context)
        options = self._generate_options(anomalies, context)
        
        if not options:
            return None

        # 3. SELECT RECOMMENDED SOLUTION
        recommended = self._select_best(options)
        
        # 4. GENERATE IMPLEMENTATION PLAN
        plan = self._generate_plan(recommended)

        return RemediationProposal(
            observation=observation,
            likely_causes=causes,
            solution_options=options,
            recommended_solution=recommended.name,
            implementation_plan=plan,
            confidence_level=recommended.confidence
        )

    def _detect_anomalies(self, ctx: Any) -> List[Dict[str, Any]]:
        anomalies = []
        # Check evidence for deviations
        for e in ctx.relevant_evidence:
            val = e.get("value")
            key = e.get("key", "")
            
            # Threshold-based detection (Simulated for latency/errors)
            if "latency" in key.lower() and isinstance(val, (int, float)) and val > 400:
                anomalies.append({"type": "latency", "key": key, "value": val})
            if "error" in key.lower() or "fail" in key.lower():
                anomalies.append({"type": "error", "key": key, "value": val})
            if "critical" in str(val).lower() or "warning" in str(val).lower():
                anomalies.append({"type": "warning", "key": key, "value": val})
                
        # Check active hypotheses for verified issues
        for h in ctx.active_hypotheses:
            if h.get("confidence", 0) > 0.7:
                 anomalies.append({"type": "hypothesis", "key": h["description"], "value": h["confidence"]})
                 
        return anomalies

    def _craft_observation(self, anomalies: List[Dict[str, Any]], ctx: Any) -> str:
        if not anomalies: return "System state appears nominal."
        
        primary = anomalies[0]
        count = len(anomalies)
        chip = ctx.relevant_chip_context[0] if ctx.relevant_chip_context else "Core"
        
        if primary["type"] == "latency":
            return f"Detected unusual latency spike ({primary['value']}ms) in {chip} module: {primary['key']}."
        elif primary["type"] == "error":
            return f"Critical state mismatch detected in {chip}. Multiple synchronization errors observed."
        
        return f"Identified {count} anomalies affecting {chip} operational stability."

    def _rank_causes(self, anomalies: List[Dict[str, Any]], ctx: Any) -> List[str]:
        causes = []
        for a in anomalies:
            if a["type"] == "latency":
                causes.append("Excessive router dispatch cycles")
                causes.append("Blocking calls in main event loop")
            elif a["type"] == "error":
                causes.append("Module synchronization race condition")
                causes.append("Stale state cache in memory provider")
            else:
                causes.append("Incomplete context assembly for complex prompts")
        return list(dict.fromkeys(causes))[:4] # Unique values

    def _generate_options(self, anomalies: List[Dict[str, Any]], ctx: Any) -> List[RemediationOption]:
        options = []
        learning = adaptive_learning.get_reliability_report()
        patterns = learning.get("top_patterns", {})
        
        # Base confidence influenced by past success
        success_bias = 0.0
        for a in anomalies:
            if a["key"] in patterns:
                success_bias += patterns[a["key"]].get("weighted_impact", 0.0)
        
        # Adjust confidence based on learning history density
        modifier = min(max(success_bias * 0.05, -0.2), 0.2)

        if any(a["type"] == "latency" for a in anomalies):
            options.append(RemediationOption(
                name="Async Dispatch Queue",
                description="Isolate internal router calls into a prioritized async execution queue.",
                risk="LOW: Possible micro-latency increment for non-priority messages.",
                confidence=round(0.75 + modifier, 2)
            ))
            options.append(RemediationOption(
                name="Router Cycle Throttling",
                description="Implement rate-limiting on high-frequency internal events.",
                risk="MEDIUM: Potential delay in real-time UI updates.",
                confidence=round(0.60 + modifier, 2)
            ))
        
        if any(a["type"] in ["error", "warning"] for a in anomalies):
            options.append(RemediationOption(
                name="State Reconciliation Handshake",
                description="Force a full integrity check and state reload across active modules.",
                risk="MEDIUM: Transient CPU burst during synchronization.",
                confidence=round(0.82 + modifier, 2)
            ))
            options.append(RemediationOption(
                name="Graceful Degradation Toggle",
                description="Disable non-essential visual updates to preserve core stability.",
                risk="LOW: Reduced UI fidelity during recovery.",
                confidence=round(0.70 + modifier, 2)
            ))

        # Default Option if needed
        if not options:
            options.append(RemediationOption(
                name="Deep Trace Collection",
                description="Enable verbose logging to isolate sub-module failure points.",
                risk="LOW: Increased log storage usage.",
                confidence=0.90
            ))

        return options

    def _select_best(self, options: List[RemediationOption]) -> RemediationOption:
        return max(options, key=lambda x: x.confidence)

    def _generate_plan(self, recommended: RemediationOption) -> List[str]:
        if "Queue" in recommended.name:
            return [
                "Initialize async worker pool",
                "Wrap blocking router dispatches in await calls",
                "Implement queue depth monitoring",
                "Validate latency reduction after 100 cycles"
            ]
        if "Handshake" in recommended.name:
            return [
                "Acquire lock on state manager",
                "Execute full-module integrity handshake",
                "Invalidate stale cache entries",
                "Verify state consistency"
            ]
        return [
            "Audit affected functions",
            "Apply patch in controlled environment",
            "Perform regression testing",
            "Promote to live runtime"
        ]

remediation_engine = RemediationEngine()
