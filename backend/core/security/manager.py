import hashlib
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.config import settings

logger = logging.getLogger(__name__)

class SecurityFortressManager:
    """
    Manages Device Trust and Security Audit Logs for the Creator.
    """
    
    def is_device_trusted(self, user_id: str, device_id: str, signature: str) -> bool:
        """
        Verifies if a device is registered and the signature matches.
        """
        with set_chip_context("core"):
            with db_manager.get_connection(internal=True) as conn:
                row = conn.execute(
                    "SELECT signature_key FROM trusted_devices WHERE user_id = ? AND device_id = ? AND is_active = 1",
                    (user_id, device_id)
                ).fetchone()
                
                if not row:
                    return False
                
                # Verify signature (Simplified for V1: hmac-like check of user_id + device_id + key)
                expected_sig = hashlib.sha256(f"{user_id}:{device_id}:{row['signature_key']}".encode()).hexdigest()
                is_valid = (signature == expected_sig)
                
                if is_valid:
                    conn.execute(
                        "UPDATE trusted_devices SET last_used_at = ? WHERE user_id = ? AND device_id = ?",
                        (datetime.utcnow().isoformat(), user_id, device_id)
                    )
                    conn.commit()
                
                return is_valid

    def register_device(self, user_id: str, device_id: str, device_name: str) -> str:
        """
        Registers a new device and returns a unique signature key.
        """
        signature_key = hashlib.sha256(f"{user_id}:{device_id}:{datetime.utcnow()}".encode()).hexdigest()
        
        with set_chip_context("core"):
            with db_manager.get_connection(internal=True) as conn:
                conn.execute(
                    """
                    INSERT INTO trusted_devices (id, user_id, device_id, device_name, signature_key)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (hashlib.md5(f"{user_id}:{device_id}".encode()).hexdigest(), user_id, device_id, device_name, signature_key)
                )
                conn.commit()
        
        return signature_key

    def log_creator_action(self, creator_id: str, action_type: str, target: str, payload: Any, device_id: str = None):
        """
        Records a signed audit entry for every creator action.
        """
        payload_str = json.dumps(payload)
        timestamp = datetime.utcnow().isoformat()
        
        # Action signature for tamper-proofing
        sig_base = f"{timestamp}:{creator_id}:{action_type}:{target}:{payload_str}"
        hash_signature = hashlib.sha256(sig_base.encode()).hexdigest()
        
        with set_chip_context("core"):
            with db_manager.get_connection(internal=True) as conn:
                conn.execute(
                    """
                    INSERT INTO security_audit_logs (creator_id, action_type, target_resource, payload_snapshot, hash_signature, device_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (creator_id, action_type, target, payload_str, hash_signature, device_id)
                )
                conn.commit()
        
        logger.info(f"SECURITY AUDIT: Creator {creator_id} performed {action_type} on {target}")

security_fortress = SecurityFortressManager()
