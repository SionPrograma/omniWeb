try:
    print("Testing import: backend.core.system_state.engine")
    from backend.core.system_state.engine import state_engine
    print("Success: state_engine imported.")
except AttributeError as e:
    print(f"FAILED with AttributeError: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"FAILED with other error: {e}")
    import traceback
    traceback.print_exc()
