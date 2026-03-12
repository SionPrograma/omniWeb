import logging
import json
from typing import Optional, List
from .education_models import Certification, UserSkill
from .skill_tracker import skill_tracker
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class CertificationEngine:
    """Awards and stores digital knowledge certifications."""
    
    def check_for_certifications(self, user_id: str) -> List[Certification]:
        """Scans user skills and awards certifications for high-level mastery."""
        skills = skill_tracker.get_user_profile()
        new_certs = []
        
        for skill in skills:
            if skill.level >= 0.9: # 90% mastery
                cert_title = f"{skill.concept.capitalize()} Mastery Certification"
                if not self._has_certification(user_id, cert_title):
                    cert = Certification(title=cert_title, user_id=user_id)
                    self._save_certification(cert)
                    new_certs.append(cert)
        
        return new_certs

    def _has_certification(self, user_id: str, title: str) -> bool:
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                row = conn.execute(
                    "SELECT id FROM certifications WHERE user_id = ? AND title = ?",
                    (user_id, title)
                ).fetchone()
                return row is not None

    def _save_certification(self, cert: Certification):
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute(
                    "INSERT INTO certifications (id, title, user_id, metadata) VALUES (?, ?, ?, ?)",
                    (cert.id, cert.title, cert.user_id, json.dumps(cert.metadata))
                )
                conn.commit()

    def get_user_certifications(self, user_id: str) -> List[Certification]:
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("SELECT * FROM certifications WHERE user_id = ?", (user_id,)).fetchall()
                return [Certification(
                    id=row["id"],
                    title=row["title"],
                    user_id=row["user_id"],
                    issue_date=row["issue_date"],
                    metadata=json.loads(row["metadata"] or "{}"),
                    verified=bool(row["verified"])
                ) for row in rows]

certification_engine = CertificationEngine()
