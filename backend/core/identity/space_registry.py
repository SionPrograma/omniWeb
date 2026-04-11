import os
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
from .models import PersonalSpace, OwnedArtifact, IdentityMapping

logger = logging.getLogger(__name__)

class SpaceRegistry:
    """
    V1.0 Block 01: Identity-to-Space Registry Foundation.
    Manages the lifecycle of governed personal spaces and isolated data roots.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SpaceRegistry, cls).__new__(cls)
            cls._instance.registry_file = os.path.join(os.getcwd(), "data", "space_registry.json")
            cls._instance.mapping_file = os.path.join(os.getcwd(), "data", "identity_mappings.json")
            cls._instance.artifacts_file = os.path.join(os.getcwd(), "data", "artifacts_registry.json")
            cls._instance._spaces: Dict[str, PersonalSpace] = {}
            cls._instance._mappings: Dict[str, IdentityMapping] = {}
            cls._instance._artifacts: List[OwnedArtifact] = []
            cls._instance._load_registry()
            cls._instance._load_mappings()
            cls._instance._load_artifacts()
        return cls._instance

    def _load_mappings(self):
        if os.path.exists(self.mapping_file):
            try:
                with open(self.mapping_file, "r") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self._mappings[k] = IdentityMapping(**v)
            except Exception as e:
                logger.error(f"[SPACE_REGISTRY] Failed to load mappings: {e}")

    def _save_mappings(self):
        os.makedirs(os.path.dirname(self.mapping_file), exist_ok=True)
        try:
            with open(self.mapping_file, "w") as f:
                data = {k: v.model_dump(mode='json') for k, v in self._mappings.items()}
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"[SPACE_REGISTRY] Failed to save mappings: {e}")

    def _load_registry(self):
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r") as f:
                    data = json.load(f)
                    for uid, sdata in data.items():
                        self._spaces[uid] = PersonalSpace(**sdata)
            except Exception as e:
                logger.error(f"[SPACE_REGISTRY] Failed to load registry: {e}")

    def _save_registry(self):
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        try:
            with open(self.registry_file, "w") as f:
                json.dump({uid: s.model_dump(mode='json') for uid, s in self._spaces.items()}, f, default=str)
        except Exception as e:
            logger.error(f"[SPACE_REGISTRY] Failed to save registry: {e}")

    def _load_artifacts(self):
        if os.path.exists(self.artifacts_file):
            try:
                with open(self.artifacts_file, "r") as f:
                    data = json.load(f)
                    self._artifacts = [OwnedArtifact(**a) for a in data]
            except Exception as e:
                logger.error(f"[SPACE_REGISTRY] Failed to load artifacts: {e}")

    def _save_artifacts(self):
        os.makedirs(os.path.dirname(self.artifacts_file), exist_ok=True)
        try:
            with open(self.artifacts_file, "w") as f:
                json.dump([a.model_dump(mode='json') for a in self._artifacts], f, indent=4)
        except Exception as e:
            logger.error(f"[SPACE_REGISTRY] Failed to save artifacts: {e}")

    def resolve_space(self, user_id: str) -> PersonalSpace:
        """
        Binds an internal identity to a governed Personal Space.
        Initializes the isolated data root if this is the first encounter.
        """
        if user_id in self._spaces:
            space = self._spaces[user_id]
            space.last_access = datetime.utcnow()
            self._save_registry()
            return space

        # Create New Personal Space
        space_id = str(uuid.uuid4())
        # Use a safe path: spaces/{user_id}/ (sovereign isolation)
        space_root = os.path.join(os.getcwd(), "spaces", user_id)
        
        # Physical Initialization (Minimal)
        os.makedirs(os.path.join(space_root, "artifacts"), exist_ok=True)
        os.makedirs(os.path.join(space_root, "memory"), exist_ok=True)
        
        new_space = PersonalSpace(
            user_id=user_id,
            space_id=space_id,
            space_root=space_root,
            identity_ref=f"omni-native:{user_id}"
        )
        
        self._spaces[user_id] = new_space
        self._save_registry()
        logger.info(f"[SPACE_REGISTRY] Initialized new Personal Space for {user_id}: {space_id}")
        return new_space

    def get_artifact_write_path(self, user_id: str, filename: str, artifact_type: str = "RESULT") -> str:
        """
        V1.0 Block 02: Safe Artifact Destination Resolver.
        Resolves the physical absolute path for a new artifact.
        Falls back to legacy /outputs if no user_id is present.
        """
        if not user_id:
            return os.path.join(os.getcwd(), "outputs", filename)
            
        space = self.resolve_space(user_id)
        # Structure: spaces/{user_id}/artifacts/{type}/{filename}
        type_dir = os.path.join(space.space_root, "artifacts", artifact_type.lower())
        os.makedirs(type_dir, exist_ok=True)
        
        return os.path.join(type_dir, filename)

    def register_artifact(self, artifact: OwnedArtifact):
        """
        Logs the ownership of a newly created artifact in the registry.
        """
        self._artifacts.append(artifact)
        self._save_artifacts()
        logger.info(f"[SPACE_REGISTRY] Registered artifact {artifact.artifact_id} for user {artifact.user_id}")

    def list_all_spaces(self) -> List[PersonalSpace]:
        """Returns all registered personal spaces (Admin/Creator use)."""
        return list(self._spaces.values())

    def get_artifact_content(self, artifact_id: str, space_id: str) -> Optional[Dict]:
        """
        V1.0 Block 04: Secure Artifact content resolver.
        Verifies ownership and reads file content safely.
        """
        # 1. Find Artifact Metadata
        artifact = next((a for a in self._artifacts if a.artifact_id == artifact_id), None)
        if not artifact or artifact.space_id != space_id:
             logger.warning(f"[SPACE_REGISTRY] Access Denied or Missing: Artifact {artifact_id} for Space {space_id}")
             return None
        
        # 2. Find Space Root
        # We need the user_id to find the space in the map
        user_id = artifact.user_id
        if user_id not in self._spaces:
             return None
             
        space = self._spaces[user_id]
        
        # 3. Resolve Path (Defensive)
        # Structure: spaces/{user_id}/artifacts/{type}/{filename}
        # relative_path should already be "artifacts/{type}/{filename}" from Block 02
        full_path = os.path.join(space.space_root, artifact.relative_path)
        
        # Security: Prevent Path Traversal
        if not full_path.startswith(space.space_root):
             logger.error(f"[SPACE_REGISTRY] Security Violation: Path Traversal detected in artifact {artifact_id}")
             return None
             
        if not os.path.exists(full_path):
             logger.warning(f"[SPACE_REGISTRY] Missing Physical File: {full_path}")
             return None
             
        # 4. Read Content
        try:
             # Handle binary vs text
             if artifact.artifact_type in ["IMAGE", "MEDIA"]:
                  import base64
                  with open(full_path, "rb") as f:
                       content = base64.b64encode(f.read()).decode('utf-8')
                       return {
                           "artifact_id": artifact_id,
                           "filename": artifact.filename,
                           "type": artifact.artifact_type,
                           "content": content,
                           "is_binary": True
                       }
             else:
                  with open(full_path, "r", encoding="utf-8") as f:
                       content = f.read()
                       return {
                           "artifact_id": artifact_id,
                           "filename": artifact.filename,
                           "type": artifact.artifact_type,
                           "content": content,
                           "is_binary": False
                       }
        except Exception as e:
             logger.error(f"[SPACE_REGISTRY] Failed to read artifact {artifact_id}: {e}")
             return None

    def resolve_external_identity(self, provider: str, external_id: str) -> str:
        """
        V1.0 Block 03: Governed External Bridge Resolver.
        Maps an authenticated external ID (e.g. Google sub) to a sovereign internal user_id.
        Initializes a Personal Space if this is a first-time entry.
        """
        key = f"{provider}:{external_id}"
        if key in self._mappings:
             mapping = self._mappings[key]
             if mapping.status == "LINKED":
                  # Verification pulse: ensure the space still exists
                  self.resolve_space(mapping.internal_id)
                  return mapping.internal_id
        
        # 1. Initialize Brand New Sovereign Identity
        internal_id = f"omni_{uuid.uuid4().hex[:8]}"
        
        # 2. Forge the Bridge
        new_mapping = IdentityMapping(
            mapping_id=f"map_{uuid.uuid4().hex[:6]}",
            provider=provider,
            external_id=external_id,
            internal_id=internal_id
        )
        self._mappings[key] = new_mapping
        self._save_mappings()
        
        # 3. Initialize the Personal Space Playground
        self.resolve_space(internal_id)
        
        logger.info(f"[SPACE_REGISTRY] Bridged {provider}:{external_id} -> {internal_id}")
        return internal_id

# Singleton
space_registry = SpaceRegistry()
