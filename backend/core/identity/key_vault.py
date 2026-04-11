import os
import logging
from cryptography.fernet import Fernet
from typing import Optional

logger = logging.getLogger(__name__)

class KeyVaultService:
    """
    V1.0 Block 04: Governed Key Vault.
    Handles encryption and persistent storage of connector secrets.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KeyVaultService, cls).__new__(cls)
            cls._instance._init_vault()
        return cls._instance

    def _init_vault(self):
        # 1. Resolve Master Key
        key_path = os.path.join(os.getcwd(), "data", "omni_master.key")
        if not os.path.exists(key_path):
             os.makedirs(os.path.dirname(key_path), exist_ok=True)
             master_key = Fernet.generate_key()
             with open(key_path, "wb") as f:
                 f.write(master_key)
             logger.warning("[KEY_VAULT] New MASTER KEY generated. Store it safely!")
        else:
             with open(key_path, "rb") as f:
                 master_key = f.read()
        
        self.cipher = Fernet(master_key)
        logger.info("[KEY_VAULT] Vault initialized and locked.")

    def encrypt_secret(self, raw_value: str) -> str:
        """Encrypts a string and returns a base64 string."""
        return self.cipher.encrypt(raw_value.encode()).decode()

    def decrypt_secret(self, encrypted_value: str) -> Optional[str]:
        """Decrypts a base64 string back to raw."""
        try:
            return self.cipher.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            logger.error(f"[KEY_VAULT_ERROR] Decryption failed: {e}")
            return None

# Singleton
key_vault = KeyVaultService()
