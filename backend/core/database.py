import sqlite3
import os
import logging
from backend.core.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Base SQLite Infrastructure for OmniWeb.
    Provides simple connection management and ensures data directory exists.
    """
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_URL
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Ensures the directory for the database file exists."""
        data_dir = os.path.dirname(self.db_path)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logger.info(f"Created data directory: {data_dir}")

    def get_connection(self):
        """
        Returns a new connection to the SQLite database.
        Recommended to use as a context manager if possible, 
        or close manually.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            # Row factory enables column access by name
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to SQLite ({self.db_path}): {e}")
            raise

    def init_db(self):
        """
        Initializes core system tables.
        """
        logger.info(f"Initializing SQLite persistence at {self.db_path}")
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_name TEXT NOT NULL,
                    payload TEXT,
                    source_chip TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        logger.info("System core tables initialized.")

# Global instance for shared access
db_manager = DatabaseManager()
