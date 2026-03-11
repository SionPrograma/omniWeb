import asyncio
import os
import sys
import sqlite3

# Ensure path
sys.path.append(os.getcwd())

from backend.core.usage.usage_tracker import usage_tracker
from backend.core.self_improvement.proposal_engine import proposal_engine
from backend.core.ai_host.command_router import ai_command_router

async def test_self_improvement():
    print("\n--- Testing Self Improvement Engine ---")
    
    # 1. Generate usage noise (3 repeated AI commands to trigger friction)
    for _ in range(3):
        await ai_command_router.route("Abrir finanzas")
    print("   [SETUP] Generated usage patterns for 'open_chip'.")

    # 2. Trigger Proposal Generation
    new_proposals = proposal_engine.generate_proposals()
    print(f"   [RUN] New proposals generated: {new_proposals}")
    
    # 3. Verify Proposals in DB
    proposals = proposal_engine.get_pending_proposals()
    print(f"   [VERIFY] Pending Proposals: {[p['description'] for p in proposals]}")
    
    assert len(proposals) > 0
    assert any("finanzas" in p["description"].lower() or "open_chip" in p["description"].lower() for p in proposals)
    print("   [PASS] Self-improvement proposals captured correctly.")

    # 4. Test AI Host Integration
    resp = await ai_command_router.route("Sugerencias de mejora")
    print(f"   [AI] AI Response: {resp.message}")
    assert resp.intent == "system_insights"
    assert "oportunidades" in resp.message.lower() or "detectado" in resp.message.lower()
    print("   [PASS] AI Host correctly reports system insights.")

if __name__ == "__main__":
    asyncio.run(test_self_improvement())
