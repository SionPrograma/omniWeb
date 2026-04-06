import sys
import os
import json
from datetime import datetime

# Set Python Path
sys.path.append(os.getcwd())

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.observability.governance_heatmap_engine import heatmap_engine

def validate_heatmap():
    print("--- OMNIPY: VALIDACIÃ“N DE HEATMAP ENGINE ---")
    
    with set_chip_context("core"):
        # 1. Clean environment for test
        with db_manager.get_connection() as conn:
            # We don't want to wipe user data, but we can check what exists
            print(f"Buscando dominios en el sistema...")
            
        # 2. Add sample data if needed (Safe injection)
        # Assuming we have some traces or overrides from previous steps
        
        # 3. Generate Heatmap
        nodes = heatmap_engine.get_friction_heatmap()
        
        print(f"Nodos detectados: {len(nodes)}")
        for node in nodes:
            print(f"\n[DOMINIO: {node.domain}]")
            print(f"  Score: {node.friction_score}")
            print(f"  Band:  {node.severity_band}")
            print(f"  Rationale: {node.rationale}")
            print(f"  Action: {node.recommended_action}")
            print(f"  Signals: {json.dumps(node.signals, indent=2)}")

    print("\n--- VALIDACIÃ“N COMPLETADA ---")

if __name__ == "__main__":
    validate_heatmap()
