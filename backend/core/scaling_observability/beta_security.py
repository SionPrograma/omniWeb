import logging
import uuid
from typing import Dict, Any, List
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class BetaController:
    """Phase 48 & 50: Beta Entry & Testing Mode."""
    async def create_invite_token(self, issuer_id: str) -> str:
        token = f"OMNI-BETA-{str(uuid.uuid4())[:8].upper()}"
        async with db_manager.get_session() as session:
            await session.execute("""
                INSERT INTO registration_tokens (token_id, token_string, issuer_id)
                VALUES (:tid, :ts, :iid)
            """, {"tid": str(uuid.uuid4()), "ts": token, "iid": issuer_id})
            await session.commit()
        return token

    async def submit_feedback(self, user_id: str, feature: str, content: str, sentiment: float = 0.5):
        async with db_manager.get_session() as session:
            await session.execute("""
                INSERT INTO beta_feedback (feedback_id, user_id, feature_slug, content, sentiment_score)
                VALUES (:fid, :uid, :slug, :content, :score)
            """, {
                "fid": str(uuid.uuid4()), "uid": user_id, "slug": feature, 
                "content": content, "score": sentiment
            })
            await session.commit()
        logger.info(f"BetaMode: Feedback received from {user_id} for {feature}")

class SecurityAuditor:
    """Phase 54: Global Security Hardening."""
    async def log_security_event(self, event_type: str, severity: str, outcome: str, details: Dict[str, Any] = {}):
        import json
        async with db_manager.get_session() as session:
            await session.execute("""
                INSERT INTO security_audit_events (event_id, event_type, severity, outcome, details)
                VALUES (:eid, :etype, :sev, :out, :det)
            """, {
                "eid": str(uuid.uuid4()), "etype": event_type, "sev": severity, 
                "out": outcome, "det": json.dumps(details)
            })
            await session.commit()
        logger.warning(f"SecurityAuditor: [{severity.upper()}] {event_type} - {outcome}")

beta_controller = BetaController()
security_auditor = SecurityAuditor()
