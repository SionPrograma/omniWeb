from typing import List, Optional
from datetime import datetime
from backend.core.database import db_manager
from .schemas import MusicIdea

class MusicRepository:
    """
    Handles SQLite persistence for chip-musica.
    Manages musical ideas and theory presets.
    """
    def __init__(self):
        self.init_db()

    def init_db(self):
        """Initializes the music_ideas table if it doesn't exist."""
        with db_manager.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS music_ideas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    scale_context TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def get_all(self) -> List[MusicIdea]:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM music_ideas ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [MusicIdea(**dict(row)) for row in rows]

    def add(self, idea: MusicIdea) -> MusicIdea:
        date_str = datetime.now().isoformat()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO music_ideas (title, content, scale_context, created_at) VALUES (?, ?, ?, ?)",
                (idea.title, idea.content, idea.scale_context, date_str)
            )
            idea.id = cursor.lastrowid
            idea.created_at = date_str
            conn.commit()
            return idea

# Global instance
music_repo = MusicRepository()
