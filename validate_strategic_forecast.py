import sys
import os
import asyncio
import json

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager
from backend.core.ai_host.processors.multimodal_processor import MultimodalProcessor

async def validate_strategic_forecast():
    print("--- VALIDATING STRATEGIC SIMULATION & FORECAST ---")
    
    processor = MultimodalProcessor()
    
    with set_chip_context("core"):
        # 1. SETUP: Ensure history exists
        from backend.core.database import db_manager
        with db_manager.get_connection(internal=True) as conn:
             # Manually insert high-value history to ensure delta is visible
             conn.execute("""
                 INSERT OR REPLACE INTO mission_learning (pattern_key, successful_action, total_roi, execution_count, confidence, last_seen)
                 VALUES ('forecast_layer:ATTENTION_REQUIRED::RESTORE_FOCUS', 'RESTORE_FOCUS', 80.0, 1, 0.9, CURRENT_TIMESTAMP)
             """)
             conn.commit()

        # 2. CREATE NEW DRIFT
        print("\n[STEP 2] Creating Forecastable Drift...")
        m = mission_manager.create_mission("Forecast Test Mission")
        await processor.process("[VISUAL_EVIDENCE] Initial", context={})
        m.multimodal_history[0]["hypothesis"] = {"layer": "forecast_layer", "description": "Base focus"}
        
        # Add drift to 100 level
        await processor.process("[VISUAL_EVIDENCE] Drifted", context={})
        m.multimodal_history[-1]["hypothesis"] = {"layer": "noisy_layer", "description": "Drifted focus"}
        mission_manager.save_mission(m)

        # 3. GET FORECAST
        print("\n[STEP 3] Fetching Strategic Forecast...")
        report = m.analyze_cognitive_drift()
        suggestions = report["suggested_actions"]
        
        # Verify
        restore_action = next((s for s in suggestions if s["type"] == "RESTORE_FOCUS"), None)
        
        if not restore_action:
             raise Exception("FAILED: RESTORE_FOCUS suggestion not found.")
             
        forecast = restore_action.get("forecast")
        if not forecast:
             raise Exception("FAILED: No forecast object in suggestion.")
             
        print(f"FORECAST FOUND: Source={forecast['source']}")
        print(f"Current: {forecast['current_drift']} | Predicted: {forecast['predicted_drift']} | Delta: {forecast['delta']}")
        print(f"Confidence: {forecast['confidence']}")

        if forecast["source"] != "HISTORICAL":
             raise Exception(f"FAILED: Forecast source should be HISTORICAL. Got {forecast['source']}")
        
        if forecast["delta"] < 40: # Expecting around 80 from our manual insert
             raise Exception(f"FAILED: Forecast delta too low. Expected improvement. Got {forecast['delta']}")

        print("\n--- STRATEGIC SIMULATION & FORECAST VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    asyncio.run(validate_strategic_forecast())
