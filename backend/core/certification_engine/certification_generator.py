import logging
import json
from typing import List, Optional
from .certification_models import Certification, SkillVerification
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class CertificationGenerator:
    """Awards formal certifications based on verified mastery levels."""
    
    def award_certification(self, user_id: str, title: str, skills: List[str], level: str = "Foundation") -> Certification:
        cert = Certification(
            title=title,
            level=level,
            user_id=user_id,
            skills_covered=skills,
            metadata={"origin": "OmniWeb Human Development Network"}
        )
        self._save(cert)
        return cert

    def _save(self, cert: Certification):
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO certifications (id, title, user_id, metadata) 
                    VALUES (?, ?, ?, ?)
                    """,
                    (cert.id, f"{cert.title} ({cert.level})", cert.user_id, json.dumps(cert.metadata))
                )
                conn.commit()

    def list_user_certs(self, user_id: str) -> List[Dict[str, Any]]:
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("SELECT * FROM certifications WHERE user_id = ?", (user_id,)).fetchall()
                return [dict(row) for row in rows]

certification_generator = CertificationGenerator()
