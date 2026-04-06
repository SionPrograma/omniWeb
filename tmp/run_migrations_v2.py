import sys
import os

sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def main():
    print("Running migrations...")
    with set_chip_context("core"):
        db_manager.run_migrations()
    print("Migrations complete.")

if __name__ == "__main__":
    main()
