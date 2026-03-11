
import os
import sys
# Add backend to path to import
sys.path.append(os.getcwd())

from backend.core.ai_developer.chip_editor import chip_editor

def test_invalid_patch():
    print("Testing invalid patch (syntax error)...")
    # chip-finanzas exists
    patches = [
        {
            "file": "core/router.py",
            "action": "append",
            "content": "\nThis is a syntax error {}{}{"
        }
    ]
    result = chip_editor.apply_patches("finanzas", patches)
    print(f"Result: {result}")
    if result["status"] == "error" and "reverted" in result["message"]:
        print("[PASS] Rollback worked after syntax error.")
    else:
        print("[FAIL] Rollback did not work as expected.")

if __name__ == "__main__":
    test_invalid_patch()
