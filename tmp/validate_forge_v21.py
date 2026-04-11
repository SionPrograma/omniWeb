import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.forge.sync import forge_cross_sync

async def validate_forge_v21():
    print("--- OMNI_INTELLIGENCE_FORGE_V2.1 Cross-Domain Sync Validation ---")
    
    with set_chip_context("core"):
        db_manager.init_db()
        
        # 1. Clear and setup sample affinity in a DIFFERENT chip
        with db_manager.get_connection(internal=True) as conn:
            conn.execute("DELETE FROM intelligence_forge_affinity_memory")
            conn.execute("DELETE FROM intelligence_forge_cross_sync_advisories")
            
            # Strong affinity in VISION chip
            conn.execute("""
                INSERT INTO intelligence_forge_affinity_memory 
                (chip_id, capability, context_tag, provider_id, affinity_score, sample_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("vision", "analysis", "low_light", "infra_model_v1", 0.9, 50))
            conn.commit()

        # 2. Trigger Scan
        print("Step 2: Triggering Cross-Domain Sync Scan...")
        await forge_cross_sync.scan_for_synergies()
        
        # 3. Verify Synergies for LINGUA
        syns = await forge_cross_sync.get_synergies("lingua")
        print(f"Captured Synergies for Lingua: {len(syns)}")
        
        if len(syns) == 0:
            print("FAIL: No cross-domain synergy captured for Lingua.")
            return False
            
        syn = syns[0]
        print(f"Source: {syn['source_chip']} | Match: {syn['capability']} | Strength: {syn['strength']}")
        
        if syn['source_chip'] != "vision":
            print("FAIL: Synergy source chip mismatch.")
            return False
            
        print("\nSUCCESS: Forge V2.1 Cross-Domain Sync validated.")
        return True

if __name__ == "__main__":
    success = asyncio.run(validate_forge_v21())
    sys.exit(0 if success else 1)
