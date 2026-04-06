from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def manual_sync():
    print("Syncing migrations manually...")
    with set_chip_context('core'):
        with db_manager.get_connection() as conn:
            # Mark 107-110 as applied
            to_mark = [
                "107_accepted_debt_dashboard.sql",
                "108_governance_fusion_snapshots.sql",
                "109_governance_action_traces.sql",
                "110_governance_trace_indexes.sql"
            ]
            for f in to_mark:
                conn.execute("INSERT OR IGNORE INTO system_migrations (filename) VALUES (?)", (f,))
            conn.commit()
            print("Marked 107-110 as applied.")
            
            # Now run 111 and 112
            print("Running 111 and 112...")
            db_manager.run_migrations()
    print("Done.")

if __name__ == "__main__":
    manual_sync()
