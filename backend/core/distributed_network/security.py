import logging
from typing import Optional
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()

class NetworkSecurity:
    """
    Handles node authentication and query permissions for the Distributed network.
    """
    def __init__(self):
        # In a real system, nodes would exchange certificates or asymmetric keys
        # For now, we use the shared OMNIWEB_ADMIN_TOKEN for node-to-node auth
        self.node_secret = settings.ADMIN_TOKEN

    async def authenticate_node(self, auth: HTTPAuthorizationCredentials = Security(security)):
        """Verifies if the incoming request is from a trusted node."""
        if auth.credentials != self.node_secret:
            logger.warning(f"NetworkSecurity: Authentication failed for remote node.")
            raise HTTPException(status_code=403, detail="Invalid node credentials")
        return True

network_security = NetworkSecurity()
