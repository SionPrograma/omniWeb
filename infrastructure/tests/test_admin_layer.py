import sys
import os
import asyncio
from datetime import datetime

# Set PYTHONPATH
sys.path.append(os.getcwd())

from backend.core.admin_logbook.manager import admin_manager
from backend.core.admin_logbook.models import AISuggestion, SuggestionStatus
from backend.core.permissions import set_chip_context
from backend.core.config import settings

async def test_admin_control():
    print("--- OmniWeb Admin Control Layer Test ---")
    
    creator_id = settings.CREATOR_ID
    admin_id = "admin_1"
    
    print(f"Setting context for {creator_id}...")
    with set_chip_context("core", user_id=creator_id):
        print("Context set. Attempting to add suggestion...")
        # 1. AI Generates Suggestion
        print("AI: Generating suggestion...")
        suggestion = AISuggestion(
            id="SUG_001",
            suggestion_type="FIX",
            content={"sector": "auth", "patch": "Update token expiry"},
            severity="warning"
        )
        print("Calling admin_manager.add_ai_suggestion...")
        try:
            admin_manager.add_ai_suggestion(suggestion)
            print("Suggestion added.")
        except Exception as e:
            print(f"Error adding suggestion: {e}")
            raise
        
        # 2. Admin Reviews Suggestion
        print("Admin: Reviewing suggestion...")
        admin_manager.review_suggestion("SUG_001", admin_id, SuggestionStatus.APPROVED, "Critical security fix")
        
        # 3. Log Admin Operation
        print("Admin: Registering operation...")
        admin_manager.log_operation(admin_id, "DEPLOY", "auth_module", {"version": "1.2.1"})
        
        # 4. Creator Creates Checkpoint
        print("Creator: Creating system checkpoint...")
        checkpoint_path = admin_manager.create_checkpoint(creator_id, "Pre-Deployment Snapshot")
        print(f"Checkpoint created at: {checkpoint_path}")
        
        # 5. List Operations
        print("\nVerifying logs:")
        logs = admin_manager.list_operations(limit=5)
        for log in logs:
            print(f"  - [{log['timestamp']}] {log['operation_type']} by {log['admin_id']} on {log['target_resource']}")
            
        # 6. Check Rollback Logic (Security check only)
        print("\nVerifying Rollback security...")
        try:
            # Try to rollback with wrong ID (simulation)
            admin_manager.rollback_to_checkpoint(1, "unauthorized_user")
        except PermissionError:
            print("  - [PASS] Unauthorized rollback blocked.")
        except Exception as e:
            print(f"  - [INFO] Rollback test: {e}")

    print("\n--- Test Complete ---")

if __name__ == "__main__":
    asyncio.run(test_admin_control())
