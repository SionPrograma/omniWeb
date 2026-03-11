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
        Placeholder for global table initialization.
        Usually called during server startup.
        """
        logger.info(f"Initializing SQLite persistence at {self.db_path}")
        # In a real scenario, we could run core table schemas here.
        pass

# Global instance for shared access
db_manager = DatabaseManager()
