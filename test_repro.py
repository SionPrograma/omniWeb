try:
    print("Testing import: backend.core.database")
    from backend.core.database import db_manager
    print("Success: database.db_manager imported.")
    
    print("Testing db_manager.get_session()")
    session = db_manager.get_session()
    print(f"Success: get_session exists: {session}")
except AttributeError as e:
    print(f"FAILED with AttributeError: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"FAILED with other error: {e}")
    import traceback
    traceback.print_exc()
