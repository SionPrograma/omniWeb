import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from backend.core.database import db_manager
from backend.core.governance.mode_registry import OmniMode

logger = logging.getLogger(__name__)

class OmniAuditLogger:
    """
    OMNIWEB — BLOQUE: OMNI_MODE_AUDIT_LOGGING_V1.4.
    Central mode-aware audit logger for tracking actions across operational boundaries.
    """

    @staticmethod
    def log_action(
        user_id: str,
        user_mode: OmniMode,
        permission_level: str,
        operation_type: str,
        target_resource: str,
        details: Dict[str, Any],
        outcome: str = "SUCCESS"
    ):
        """
        Records a mode-aware audit entry in the admin_operations ledger.
        """
        try:
            with db_manager.get_connection(internal=True) as conn:
                conn.execute("""
                    INSERT INTO admin_operations (
                        admin_id, user_mode, permission_level, 
                        operation_type, target_resource, details, outcome
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, 
                    user_mode.value if hasattr(user_mode, 'value') else str(user_mode),
                    permission_level,
                    operation_type,
                    target_resource,
                    json.dumps(details),
                    outcome
                ))
                conn.commit()
            
            # Mission Log for visibility
            log_msg = f"AUDIT: [{user_mode}] {user_id} performed {operation_type} on {target_resource} -> {outcome}"
            if outcome == "FAILURE":
                logger.warning(log_msg)
            else:
                logger.info(log_msg)
                
        except Exception as e:
            logger.error(f"Audit Logger: Failed to record action: {e}")

    @staticmethod
    def log_security_event(
        creator_id: str,
        user_mode: OmniMode,
        action_type: str,
        target: str,
        payload: Any,
        outcome: str = "SUCCESS"
    ):
        """
        Bridge to security_fortress with mode-awareness.
        """
        import hashlib
        payload_str = json.dumps(payload)
        timestamp = datetime.utcnow().isoformat()
        
        # Action signature for tamper-proofing
        sig_base = f"{timestamp}:{creator_id}:{action_type}:{target}:{payload_str}"
        hash_signature = hashlib.sha256(sig_base.encode()).hexdigest()
        
        try:
            with db_manager.get_connection(internal=True) as conn:
                conn.execute("""
                    INSERT INTO security_audit_logs (
                        creator_id, user_mode, action_type, 
                        target_resource, payload_snapshot, hash_signature, outcome
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    creator_id,
                    user_mode.value if hasattr(user_mode, 'value') else str(user_mode),
                    action_type,
                    target,
                    payload_str,
                    hash_signature,
                    outcome
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Audit Logger: Failed to record security event: {e}")

audit_logger = OmniAuditLogger()
