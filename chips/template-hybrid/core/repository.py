from backend.core.database import db_manager
import logging

logger = logging.getLogger(__name__)

class TemplateRepository:
    def __init__(self):
        # OBLIGATORIO: No llamar a la DB aquí (Import-time side effects prohibidos)
        self._initialized = False

    def _ensure_initialized(self):
        """Patrón de naturalización: Inicialización diferida."""
        if not self._initialized:
            logger.info("TEMPLATE-CHIP: Realizando inicialización diferida...")
            self.init_db()
            self._initialized = True

    def init_db(self):
        """Crea las tablas necesarias si no existen."""
        with db_manager.get_connection() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS template_items (id INTEGER PRIMARY KEY, name TEXT)")
            conn.commit()

    def get_data(self):
        self._ensure_initialized()
        with db_manager.get_connection() as conn:
            return conn.execute("SELECT * FROM template_items").fetchall()

template_repo = TemplateRepository()
