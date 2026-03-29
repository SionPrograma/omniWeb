
import uuid
import time
import logging
import json
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)

class TraceObservation(BaseModel):
    name: str
    start_time: float
    end_time: Optional[float] = None
    input: Any = None
    output: Any = None
    status: str = "success"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def latency(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return 0.0

class InteractionTrace(BaseModel):
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.isoformat(datetime.now()))
    user_input: str
    detected_intent_group: Optional[str] = None
    detected_specific_intent: Optional[str] = None
    response_mode: Optional[str] = None
    candidate_tools: List[str] = Field(default_factory=list)
    selected_tool: Optional[str] = None
    memory_refs_count: int = 0
    final_response: Optional[str] = None
    status: str = "processing" # success, fallback, error
    latency_total: float = 0.0
    observations: List[TraceObservation] = Field(default_factory=list)
    diagnostics: List[str] = Field(default_factory=list)

class TracingAPI:
    """
    Observability Layer for OmniWeb AI Host.
    Captures traces and observations for internal auditing and evaluation.
    Designed for future Langfuse compatibility.
    """
    def __init__(self):
        self._active_traces: Dict[str, InteractionTrace] = {}
        # Simple in-memory buffer for recent traces (to avoid DB overhead in this block)
        self._trace_buffer: List[InteractionTrace] = []
        self._max_buffer = 100

    def start_trace(self, user_input: str) -> str:
        try:
            trace = InteractionTrace(user_input=user_input)
            self._active_traces[trace.trace_id] = trace
            return trace.trace_id
        except Exception as e:
            logger.error(f"[TRACING] Failed to start trace: {e}")
            return "error_trace"

    def get_trace(self, trace_id: str) -> Optional[InteractionTrace]:
        return self._active_traces.get(trace_id)

    def start_observation(self, trace_id: str, name: str, input_data: Any = None) -> None:
        trace = self.get_trace(trace_id)
        if not trace: return
        obs = TraceObservation(name=name, start_time=time.time(), input=input_data)
        trace.observations.append(obs)

    def end_observation(self, trace_id: str, name: str, output_data: Any = None, status: str = "success", metadata: Optional[Dict[str, Any]] = None) -> None:
        trace = self.get_trace(trace_id)
        if not trace: return
        for obs in reversed(trace.observations):
            if obs.name == name and obs.end_time is None:
                obs.end_time = time.time()
                obs.output = output_data
                obs.status = status
                if metadata:
                    obs.metadata.update(metadata)
                break

    def finalize_trace(self, trace_id: str, final_response: str, final_status: str = "success") -> Optional[InteractionTrace]:
        trace = self._active_traces.pop(trace_id, None)
        if not trace: return None
        
        try:
            trace.final_response = final_response
            trace.status = final_status
            
            # Calculate total latency
            if trace.observations:
                total_start = trace.observations[0].start_time
                total_end = trace.observations[-1].end_time or time.time()
                trace.latency_total = total_end - total_start
            
            # Map observations to top-level fields for easy indexing
            for obs in trace.observations:
                if obs.name == "intent_understanding" and obs.output:
                    trace.detected_intent_group = obs.output.get("intent_group")
                    trace.detected_specific_intent = obs.output.get("specific_intent")
                    trace.response_mode = obs.output.get("mode")
                elif obs.name == "retrieve_memory" and obs.output:
                    trace.memory_refs_count = len(obs.output)
                elif obs.name == "select_tools" and obs.output:
                    trace.selected_tool = obs.output
                    if obs.metadata and "candidates" in obs.metadata:
                        trace.candidate_tools = obs.metadata["candidates"]
            
            # Buffer it
            self._trace_buffer.append(trace)
            if len(self._trace_buffer) > self._max_buffer:
                self._trace_buffer.pop(0)
            
            # Silent log for auditing
            logger.info(f"[TRACING] Trace Finalized | ID: {trace.trace_id} | Intent: {trace.detected_intent_group} | Status: {trace.status}")
            return trace
        except Exception as e:
            logger.error(f"[TRACING] Error finalizing trace: {e}")
            return trace

    def get_recent_traces(self, limit: int = 10) -> List[InteractionTrace]:
        return self._trace_buffer[-limit:]

tracing_api = TracingAPI()
