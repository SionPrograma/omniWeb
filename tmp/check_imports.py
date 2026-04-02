import sys
import os

# Root of the project is the parent of 'tmp'
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root)

try:
    print("Trying to import CognitiveOrchestrator...")
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    print("SUCCESS: CognitiveOrchestrator imported.")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
