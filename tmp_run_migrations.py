from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def run():
    print("Running OmniWeb DB migrations...")
    with set_chip_context('core'):
        db_manager.run_migrations()
    print("Done.")

if __name__ == "__main__":
    run()
