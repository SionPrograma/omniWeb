import asyncio
import sys
import os
import sqlite3

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.core.database import db_manager

async def migrate():
    with db_manager.get_connection(internal=True) as conn:
        try:
            conn.execute("ALTER TABLE intelligence_forge_affinity_memory ADD COLUMN chip_id TEXT DEFAULT 'lingua'")
            conn.commit()
            print("Successfully migrated chip_id column.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
