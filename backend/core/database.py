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
        # Integra el modelo operativo de permisos de chip.
        from backend.core.permissions import enforce_permission
        
        try:
            enforce_permission("db_access")
        except Exception as e:
            logger.error(f"Module attempted unauthorized DB access: {e}")
            raise

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

    def run_migrations(self):
        """
        Executes raw SQL migration files inside backend/data/migrations.
        Ensures versioned schema evolutions.
        """
        data_dir = os.path.dirname(self.db_path)
        migrations_dir = os.path.join(data_dir, "migrations")
        os.makedirs(migrations_dir, exist_ok=True)
            
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            
            applied = {row["filename"] for row in conn.execute("SELECT filename FROM system_migrations")}
            files = sorted([f for f in os.listdir(migrations_dir) if f.endswith(".sql")])
            for file in files:
                if file not in applied:
                    logger.info(f"Applying DB migration: {file}")
                    with open(os.path.join(migrations_dir, file), "r", encoding="utf-8") as f:
                        sql = f.read()
                    
                    try:
                        conn.executescript(sql)
                        conn.execute("INSERT INTO system_migrations (filename) VALUES (?)", (file,))
                        conn.commit()
                    except Exception as e:
                        logger.error(f"Migration {file} failed: {e}")
                        conn.rollback()
                        raise

    def backup_db(self, destination_path: str = None) -> str:
        """
        Creates a consistent online backup of the SQLite database.
        Returns the absolute path to the backup file.
        """
        import time
        if not destination_path:
            filename = f"omniweb_backup_{int(time.time())}.db"
            data_dir = os.path.dirname(self.db_path)
            destination_path = os.path.join(data_dir, "backups", filename)
            
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        logger.info(f"Creating DB backup at {destination_path}")
        # Note: We use sqlite3.connect directly here to bypass standard permission checks
        # as this is a core infrastructural operation, but we still do it safely.
        with sqlite3.connect(self.db_path) as source:
            with sqlite3.connect(destination_path) as dest:
                source.backup(dest)
                
        logger.info("DB backup completed successfully.")
        return destination_path

    def restore_db(self, source_path: str):
        """
        Restores the main database from a backup file path.
        Uses the backup API to safely overwrite the current database online.
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Backup file not found: {source_path}")

        logger.warning(f"Restoring database from {source_path}...")
        
        # We use direct connections to bypass permission logic for this critical operation
        with sqlite3.connect(source_path) as source:
            with sqlite3.connect(self.db_path) as dest:
                source.backup(dest)
                
        logger.info("Database restoration complete.")

# Global instance for shared access
db_manager = DatabaseManager()
