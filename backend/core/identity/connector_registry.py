import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from .models import ExternalConnector, CapabilityClass
from .key_vault import key_vault

logger = logging.getLogger(__name__)

class ConnectorRegistry:
    """
    V1.0 Block 01: External Connector Registry.
    Manages the metadata and governance lifecycle of subordinate tools.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectorRegistry, cls).__new__(cls)
            cls._instance.registry_file = os.path.join(os.getcwd(), "data", "connector_registry.json")
            cls._instance._connectors: Dict[str, ExternalConnector] = {}
            cls._instance._load_registry()
        return cls._instance

    def _load_registry(self):
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r") as f:
                    data = json.load(f)
                    for cid, cdata in data.items():
                        self._connectors[cid] = ExternalConnector(**cdata)
            except Exception as e:
                logger.error(f"[CONNECTOR_REGISTRY] Failed to load: {e}")

    def _save_registry(self):
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        try:
            with open(self.registry_file, "w") as f:
                json.dump({cid: c.model_dump(mode='json') for cid, c in self._connectors.items()}, f, indent=4)
        except Exception as e:
            logger.error(f"[CONNECTOR_REGISTRY] Failed to save: {e}")

    def register_connector(self, connector: ExternalConnector) -> ExternalConnector:
        """Adds or updates a governed connector with automated vaulting."""
        # V1.0 Block 04: Secure Secrets Foundation
        for k, v in connector.config.items():
             if self._is_sensitive(k) and not v.startswith("VAULT:"):
                  encrypted_val = key_vault.encrypt_secret(v)
                  connector.config[k] = f"VAULT:{encrypted_val}"
                  
        self._connectors[connector.connector_id] = connector
        self._save_registry()
        logger.info(f"[CONNECTOR_REGISTRY] Registered {connector.connector_id} (Vaulted) for space {connector.owner_space_id}")
        return connector

    def _is_sensitive(self, key_name: str) -> bool:
        """Determines if a config field should be encrypted."""
        sensitive_suffixes = ["_secret", "_key", "_token", "password", "api_key"]
        return any(key_name.lower().endswith(s) or s in key_name.lower() for s in sensitive_suffixes)

    def update_connector_status(self, connector_id: str, status: str, user_space_id: str) -> bool:
        """
        V1.0 Block 03: Governed Lifecycle Management.
        Updates status (ACTIVE/SUSPENDED/REVOKED) if the space_id matches.
        """
        if connector_id in self._connectors:
             conn = self._connectors[connector_id]
             if conn.owner_space_id == user_space_id:
                  conn.status = status
                  conn.updated_at = datetime.utcnow()
                  self._save_registry()
                  logger.info(f"[CONNECTOR_REGISTRY] {connector_id} state changed to {status}")
                  return True
        return False

    def get_connectors_for_space(self, space_id: str) -> List[ExternalConnector]:
        """Returns all connectors bound to a specific Personal Space."""
        return [c for c in self._connectors.values() if c.owner_space_id == space_id]

    def get_connector(self, connector_id: str) -> Optional[ExternalConnector]:
        return self._connectors.get(connector_id)

# Singleton
connector_registry = ConnectorRegistry()
