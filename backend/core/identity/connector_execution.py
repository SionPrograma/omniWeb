import logging
import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from .models import ExternalConnector, ConnectorExecutionResult, CapabilityClass, OwnedArtifact
from .connector_registry import connector_registry
from .space_registry import space_registry
from .key_vault import key_vault

logger = logging.getLogger(__name__)

class GovernedExecutionWrapper:
    """
    V1.0 Block 02: Governed Tool Execution boundary.
    Wraps all external/local connector calls to ensure evidence capture
    and space-level isolation.
    """
    
    def execute(self, user_id: str, connector_id: str, action: str, params: Dict[str, Any]) -> ConnectorExecutionResult:
        """
        Main governed entry point for any external tool call.
        """
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        # 1. Authority Check
        connector = connector_registry.get_connector(connector_id)
        if not connector:
             return self._fail(execution_id, connector_id, user_id, "Connector not registered.")
             
        if connector.owner_space_id != space_registry.resolve_space(user_id).space_id:
             return self._fail(execution_id, connector_id, user_id, "Space ownership mismatch.")
             
        if connector.status != "ACTIVE":
             return self._fail(execution_id, connector_id, user_id, f"Connector is {connector.status}.")

        # 2. Capability Gate
        if action == "WRITE" and connector.capability == CapabilityClass.READ_ONLY:
             return self._fail(execution_id, connector_id, user_id, "Insufficient capabilities for WRITE action.")

        # 3. Resolve Secrets (JIT)
        # Block 04: Secrets are resolved JIT for execution but never touch the persistence layer.
        resolved_config = self._resolve_secrets(connector.config)

        # 4. Execution Simulation (Base implementation)
        # In Block 02, we demonstrate capture. We assume the 'mock' execution 
        # generates a file result.
        try:
            logger.info(f"[GOVERNED_EXEC] Running {connector_id} for user {user_id}...")
            
            # Simulated File Content (e.g. from an API fetching data)
            mock_content = f"### External DATA from {connector_id}\nTarget: {params.get('target')}\nTimestamp: {datetime.now()}"
            filename = f"capture_{execution_id}.md"
            
            # Resolve physical destination in Personal Space
            path = space_registry.get_artifact_write_path(user_id, filename, "external")
            
            # Physical Write
            with open(path, "w", encoding="utf-8") as f:
                f.write(mock_content)
                
            # 4. Artifact Registration
            artifact = OwnedArtifact(
                artifact_id=f"art_{execution_id}",
                user_id=user_id,
                space_id=connector.owner_space_id,
                artifact_type="EXTERNAL_RESULT",
                filename=filename,
                relative_path=os.path.relpath(path, os.getcwd())
            )
            space_registry.register_artifact(artifact)
            
            result = ConnectorExecutionResult(
                execution_id=execution_id,
                connector_id=connector_id,
                user_id=user_id,
                status="SUCCESS",
                message=f"Execution completed. Captured {filename} into Personal Space.",
                artifact_ids=[artifact.artifact_id],
                technical_trace={"path": path, "action": action}
            )
            self._log_to_history(user_id, result)
            return result

        except Exception as e:
            logger.error(f"[GOVERNED_EXEC_ERROR] {e}")
            res = self._fail(execution_id, connector_id, user_id, f"System error: {str(e)}")
            self._log_to_history(user_id, res)
            return res

    def _resolve_secrets(self, config: Dict[str, str]) -> Dict[str, str]:
        """Decrypts any vault references for use in execution."""
        resolved = config.copy()
        for k, v in resolved.items():
            if v.startswith("VAULT:"):
                # One-way resolution: Raw secret never leaves this boundary.
                decrypted = key_vault.decrypt_secret(v[6:])
                resolved[k] = decrypted if decrypted else "[DECRYPTION_FAILED]"
        return resolved

    def _fail(self, eid: str, cid: str, uid: str, msg: str) -> ConnectorExecutionResult:
        logger.warning(f"[GOVERNED_EXEC_DENIED] {cid} for {uid}: {msg}")
        return ConnectorExecutionResult(
            execution_id=eid,
            connector_id=cid,
            user_id=uid,
            status="DENIED",
            message=msg
        )

    def _log_to_history(self, user_id: str, result: ConnectorExecutionResult):
        """
        V1.0 Block 03: Sovereign Audit Trail.
        Persists results into the user's private space memory.
        """
        try:
            space = space_registry.resolve_space(user_id)
            history_file = os.path.join(space.space_root, "memory", "external_history.jsonl")
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(result.model_dump(mode='json')) + "\n")
        except Exception as e:
            logger.error(f"[HISTORY_LOG_ERROR] {e}")

    def get_execution_history(self, user_id: str, limit: int = 10) -> List[ConnectorExecutionResult]:
        """
        Retrieves the last N records from the user's private audit log.
        """
        import json
        history = []
        try:
            space = space_registry.resolve_space(user_id)
            history_file = os.path.join(space.space_root, "memory", "external_history.jsonl")
            if not os.path.exists(history_file): return []
            with open(history_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    history.append(ConnectorExecutionResult(**json.loads(line)))
        except Exception as e:
            logger.error(f"[HISTORY_GET_ERROR] {e}")
        return history[::-1]

# Singleton
governed_executor = GovernedExecutionWrapper()
