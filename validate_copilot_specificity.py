import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.core.ai_host.processors.proposal_processor import ProposalProcessor

async def validate():
    processor = ProposalProcessor()
    
    files_to_test = [
        "frontend/shell/main.js",
        "frontend/shell/editor.js"
    ]
    
    print("=== OMNIWEB COPILOT SPECIFICITY VALIDATION ===\n")
    
    for rel_path in files_to_test:
        abs_path = os.path.abspath(rel_path)
        print(f"Testing file: {rel_path}")
        
        # Simulate multimodal context
        context = {
            "multimodal_evidence": [
                {
                    "type": "current_file",
                    "path": abs_path
                }
            ]
        }
        
        # Prompt doesn't matter much as long as it's a general request
        # since we want to see the "proactive" audit results.
        msg = "Respondé SOLO con: MICROFIX_PROPUESTO: IMPACTO_RELACIONADO:"
        
        response = await processor.process(msg, context=context)
        
        print(f"--- OUTPUT FOR {rel_path} ---")
        # Extract the specific lines we care about
        lines = response.message.splitlines()
        for line in lines:
            if "MICROFIX_PROPUESTO" in line or "IMPACTO_RELACIONADO" in line:
                print(line)
        print("\n")

if __name__ == "__main__":
    asyncio.run(validate())
