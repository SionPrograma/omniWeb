from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def initialize():
    print("Initializing Database...")
    with set_chip_context("core"):
        db_manager.init_db()
    print("Done.")

if __name__ == "__main__":
    initialize()
