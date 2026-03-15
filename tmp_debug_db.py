import sys
sys.path.append(r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb")
from backend.core.database import db_manager, DatabaseManager
print(f"db_manager type: {type(db_manager)}")
print(f"Has get_session: {hasattr(db_manager, 'get_session')}")
print(f"Methods in db_manager: {[m for m in dir(db_manager) if not m.startswith('_')]}")
