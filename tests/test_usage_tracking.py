import asyncio
import os
import sys
import json

# Ensure path
sys.path.append(os.getcwd())

from backend.core.usage.usage_tracker import usage_tracker
from backend.core.event_bus import event_bus
from backend.core.ai_host.command_router import ai_command_router

async def test_usage_tracking():
    print("\n--- Testing Usage Tracking & Analytics ---")
    
    # 1. Manually log an event
    usage_tracker.log_event("test_manual_event", chip_slug="test-chip", metadata={"info": "test"})
    print("   [PASS] Manual event logged.")

    # 2. Trigger through Event Bus
    await event_bus.publish("test_bus_event", {"source_chip": "test-bus", "data": 123})
    print("   [PASS] Event published to bus (should be tracked).")

    # 3. Trigger through AI Host
    await ai_command_router.route("Estado del sistema")
    print("   [PASS] AI command processed (should be tracked).")

    # 4. Fetch statistics
    stats = usage_tracker.get_statistics()
    print(f"Stats: {stats}")
    
    assert stats["total_events"] >= 3
    assert any(c["slug"] == "test-chip" for c in stats["top_chips"])
    assert "test_manual_event" in stats["event_distribution"]
    assert "test_bus_event" in stats["event_distribution"]
    assert "ai_command_executed" in stats["event_distribution"]
    
    print("   [PASS] Statistics correctly computed and verified.")

if __name__ == "__main__":
    asyncio.run(test_usage_tracking())
