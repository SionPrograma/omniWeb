import logging
from typing import Dict, Any, List, Optional
from .supercommand_models import SuperCommandResult

logger = logging.getLogger(__name__)

class ResultSummarizer:
    """Generates human-readable output summarizing task results for the dashboard and interaction."""
    
    def summarize(self, result: SuperCommandResult) -> str:
        """Constructs a professional summary message of the task outcome."""
        status = "COMPLETED" if result.success else "FAILED"
        summary_msg = f"Task Execution {status}\n\n"
        summary_msg += f"Summary: {result.summary}\n"
        
        if result.issues_detected:
            summary_msg += "\nDetected Issues:\n"
            for issue in result.issues_detected:
                summary_msg += f"- {issue}\n"
        
        if result.actions_performed:
            summary_msg += "\nActions Performed:\n"
            # Show last 3 actions for brevity if many
            actions = result.actions_performed[-3:]
            for action in actions:
                summary_msg += f"- {action}\n"
                
        if result.stability_verified:
            summary_msg += "\n✅ System stability verified after execution."
        else:
            summary_msg += "\n🛑 System state may require manual audit."
            
        return summary_msg

result_summarizer = ResultSummarizer()
