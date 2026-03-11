import asyncio
import os
import sys
import datetime

# Ensure path
sys.path.append(os.getcwd())

from backend.core.usage.usage_tracker import usage_tracker
from backend.core.user_context.habit_detector import habit_detector
from backend.core.user_context.routine_analyzer import routine_analyzer
from backend.core.user_context.preference_engine import preference_engine
from backend.core.user_context.context_model import context_model
from backend.core.ai_host.command_router import ai_command_router

async def test_user_context():
    print("\n--- Testing Personal Context Engine ---")
    
    # 1. Generate usage noise for habits (Open finanzas then opens musica 3 times)
    for _ in range(3):
        usage_tracker.log_event("chip_opened", "finanzas")
        usage_tracker.log_event("chip_opened", "musica")
    
    print("   [SETUP] Generated habit data.")
    habit_detector.detect_habits()
    
    # 2. Verify habit detection
    patterns = context_model.get_patterns("habit")
    print(f"   [VERIFY] Habits detected: {len(patterns)}")
    assert len(patterns) > 0
    assert "finanzas" in patterns[0]["data"]["chips"]
    print("   [PASS] Habits captured.")

    # 3. Test Preference Engine
    preference_engine.detect_preferences()
    prefs = context_model.get_patterns("preference")
    print(f"   [VERIFY] Preferences: {len(prefs)}")
    assert len(prefs) > 0
    print("   [PASS] Preferences captured.")

    # 4. Test Routine Analyzer
    # We can't easily mock system time without a library like freezegun, 
    # but we can check if it runs without error.
    routine_analyzer.detect_routines()
    print("   [PASS] Routine analyzer executed.")

    # 5. Test AI Host Integration
    resp = await ai_command_router.route("Sugerirme una sesión")
    print(f"   [AI] Response: {resp.message}")
    assert resp.intent == "suggest_context"
    print("   [PASS] AI Host context suggestion integrated.")

if __name__ == "__main__":
    asyncio.run(test_user_context())
