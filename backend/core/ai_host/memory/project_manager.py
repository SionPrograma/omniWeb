import logging
import os
import json
import time
import uuid
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from ..synthesis.synthesis_engine import ProjectDraft, synthesis_engine
from .knowledge_graph import knowledge_graph

logger = logging.getLogger(__name__)

class ProjectLineage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_slug: str
    source_cluster_id: Optional[str] = None
    source_node_ids: List[str] = []
    source_draft_id: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    related_events: List[Dict[str, Any]] = []

class ProjectManager:
    """
    Handles the physical initialization of projects based on synthesized drafts.
    Converts a ProjectDraft into a structured 'Chip' directory in OmniWeb.
    """
    def __init__(self, base_chips_path: str = None):
        if base_chips_path is None:
            # Absolute path to chips directory
            self.base_chips_path = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb\chips"
        else:
            self.base_chips_path = base_chips_path
        self.lineages: Dict[str, ProjectLineage] = {}
        self._load_lineages()

    def _load_lineages(self):
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    rows = conn.execute("SELECT * FROM ai_host_project_lineage").fetchall()
                    for row in rows:
                        lineage = ProjectLineage(
                            id=row["id"],
                            project_slug=row["project_slug"],
                            source_cluster_id=row["source_cluster_id"],
                            source_node_ids=json.loads(row["source_node_ids"]) if row["source_node_ids"] else [],
                            source_draft_id=row["source_draft_id"],
                            created_at=row["created_at"],
                            updated_at=row["updated_at"],
                            related_events=json.loads(row["related_events"]) if row["related_events"] else []
                        )
                        self.lineages[lineage.project_slug] = lineage
            logger.info(f"[LINEAGE_LOAD] Loaded {len(self.lineages)} lineage entries.")
        except Exception as e:
            logger.error(f"[LINEAGE_LOAD_ERROR] {e}")

    def initialize_project(self, draft: ProjectDraft) -> Dict[str, Any]:
        """
        Creates the folder structure and boilerplate files for a project.
        """
        # 1. Determine Folder Name (e.g. chip-logistica)
        folder_name = f"chip-{draft.title.split(': ')[-1].lower().replace(' ', '-')}"
        project_path = os.path.join(self.base_chips_path, folder_name)

        if os.path.exists(project_path):
            return {"status": "error", "message": f"Project folder '{folder_name}' already exists."}

        try:
            # 2. Basic Structure
            os.makedirs(project_path, exist_ok=True)
            os.makedirs(os.path.join(project_path, "core"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "frontend"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "shared"), exist_ok=True)

            # 3. Create README.md
            readme_content = f"""# {draft.title}
            
## Summary
{draft.summary}

## Architecture (Suggested)
{chr(10).join(['- ' + m for m in draft.suggested_modules])}

## Next Steps
{chr(10).join([str(i+1) + '. ' + step for i, step in enumerate(draft.suggested_next_steps)])}

---
*Initialized by OmniWeb AI Host on {time.ctime(draft.created_at)}*
"""
            with open(os.path.join(project_path, "README.md"), "w", encoding="utf-8") as f:
                f.write(readme_content)

            # 4. Create chip.json
            chip_metadata = {
                "id": folder_name,
                "slug": folder_name.replace("chip-", ""),
                "name": draft.title.split(": ")[-1],
                "version": "0.1.0",
                "description": draft.summary[:200],
                "author": "OmniWeb AI Host",
                "entry_point": "core/main.py",
                "dependencies": []
            }
            with open(os.path.join(project_path, "chip.json"), "w", encoding="utf-8") as f:
                json.dump(chip_metadata, f, indent=4)

            # 5. Create core/main.py boilerplate
            core_main = f"""
import logging

logger = logging.getLogger(__name__)

class {draft.title.split(': ')[-1].replace(' ', '')}Core:
    def __init__(self):
        self.name = "{draft.title.split(': ')[-1]}"
        
    def run(self):
        logger.info(f"Initializing {{self.name}} core logic.")
        return True

if __name__ == "__main__":
    core = {draft.title.split(': ')[-1].replace(' ', '')}Core()
    core.run()
"""
            with open(os.path.join(project_path, "core", "main.py"), "w", encoding="utf-8") as f:
                f.write(core_main)

            # 6. Record Lineage
            lineage = ProjectLineage(
                project_slug=folder_name.replace("chip-", ""),
                source_cluster_id=draft.source_cluster_id,
                source_node_ids=draft.source_node_ids,
                source_draft_id=draft.id,
                related_events=[{"type": "initialized", "timestamp": time.time(), "message": "Project scaffolded."}]
            )
            self.lineages[lineage.project_slug] = lineage
            self._persist_lineage(lineage)

            # 7. Knowledge Feedback Loop: Create Project Node in Graph
            project_node = knowledge_graph.store_knowledge_node(
                title=f"Proyecto: {draft.title.split(': ')[-1]}",
                content=f"Proyecto físico inicializado en '{folder_name}'. Basado en el cluster de {draft.source_cluster_id}.",
                tags=["proyecto", "chip", "lineage"]
            )
            # Link project node to source nodes
            for node_id in draft.source_node_ids:
                knowledge_graph.link_knowledge_nodes(project_node.id, node_id)

            # 8. Log success to auditor
            self._log_initialization(draft, folder_name)

            logger.info(f"[PROJECT_INIT] Successfully initialized project at {project_path}")
            return {
                "status": "success", 
                "message": f"Project '{draft.title}' initialized successfully as '{folder_name}'. Lineage recorded and Knowledge Graph updated.",
                "path": project_path,
                "project_slug": folder_name.replace("chip-", ""),
                "lineage": lineage.model_dump()
            }

        except Exception as e:
            logger.error(f"[PROJECT_INIT_ERROR] {e}")
            return {"status": "error", "message": f"Failed to initialize project: {str(e)}"}

    def _persist_lineage(self, lineage: ProjectLineage):
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    # Validate foreign keys manually to avoid hard fails if IDs don't exist
                    # (e.g. temporary builder drafts)
                    source_cluster = None
                    if lineage.source_cluster_id:
                        chk = conn.execute("SELECT id FROM ai_host_clusters WHERE id = ?", (lineage.source_cluster_id,)).fetchone()
                        if chk: source_cluster = lineage.source_cluster_id
                    
                    source_draft = None
                    if lineage.source_draft_id:
                        chk = conn.execute("SELECT id FROM ai_host_project_drafts WHERE id = ?", (lineage.source_draft_id,)).fetchone()
                        if chk: source_draft = lineage.source_draft_id

                    conn.execute("""
                        INSERT OR REPLACE INTO ai_host_project_lineage 
                        (id, project_slug, source_cluster_id, source_node_ids, source_draft_id, created_at, updated_at, related_events)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        lineage.id, lineage.project_slug, source_cluster,
                        json.dumps(lineage.source_node_ids), source_draft,
                        lineage.created_at, lineage.updated_at, json.dumps(lineage.related_events)
                    ))
                    conn.commit()
        except Exception as e:
            logger.error(f"[LINEAGE_PERSIST_ERROR] {e}")

    def get_lineage(self, project_slug: str) -> Optional[ProjectLineage]:
        return self.lineages.get(project_slug)

    def _log_initialization(self, draft: ProjectDraft, folder_name: str):
        try:
            from backend.core.system_auditor.auditor import auditor
            auditor.log_entry(
                "INFO",
                f"Project Initialized: {draft.title} (Folder: {folder_name})",
                "ai-host",
                {"draft_id": draft.id, "folder": folder_name, "type": "project_init"}
            )
        except Exception:
            pass

project_manager = ProjectManager()
