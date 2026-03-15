import logging
import uuid
import time
import json
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from ..memory.knowledge_graph import knowledge_graph
from ..memory.cluster_manager import IdeaCluster, cluster_manager

logger = logging.getLogger(__name__)

class ProjectDraft(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    summary: str
    source_cluster_id: Optional[str] = None
    source_node_ids: List[str] = []
    suggested_modules: List[str] = []
    suggested_next_steps: List[str] = []
    created_at: float = Field(default_factory=time.time)

class EvolutionReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_slug: str
    title: str
    summary: str
    source_cluster_id: Optional[str] = None
    source_node_ids: List[str] = []
    lineage_ids: List[str] = []
    activity_event_ids: List[str] = []
    suggested_next_steps: List[str] = []
    created_at: float = Field(default_factory=time.time)

class SynthesisEngine:
    """
    Generates summaries and project drafts from idea clusters.
    """
    def __init__(self):
        self.drafts: Dict[str, ProjectDraft] = {}
        self.reports: Dict[str, EvolutionReport] = {}
        self._load_drafts()
        self._load_reports()

    def _load_reports(self):
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    rows = conn.execute("SELECT * FROM ai_host_evolution_reports").fetchall()
                    for row in rows:
                        report = EvolutionReport(
                            id=row["id"],
                            project_slug=row["project_slug"],
                            title=row["title"],
                            summary=row["summary"],
                            source_cluster_id=row["source_cluster_id"],
                            source_node_ids=json.loads(row["source_node_ids"]) if row["source_node_ids"] else [],
                            lineage_ids=json.loads(row["lineage_ids"]) if row["lineage_ids"] else [],
                            activity_event_ids=json.loads(row["activity_event_ids"]) if row["activity_event_ids"] else [],
                            suggested_next_steps=json.loads(row["suggested_next_steps"]) if row["suggested_next_steps"] else [],
                            created_at=row["created_at"]
                        )
                        self.reports[report.id] = report
            logger.info(f"[REPORTS_LOAD] Loaded {len(self.reports)} evolution reports.")
        except Exception as e:
            logger.error(f"[REPORTS_LOAD_ERROR] {e}")

    def get_reports_by_project(self, slug: str) -> List[EvolutionReport]:
        return [r for r in self.reports.values() if r.project_slug == slug]

    def _load_drafts(self):
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    rows = conn.execute("SELECT * FROM ai_host_project_drafts").fetchall()
                    for row in rows:
                        draft = ProjectDraft(
                            id=row["id"],
                            title=row["title"],
                            summary=row["summary"],
                            source_cluster_id=row["source_cluster_id"],
                            source_node_ids=json.loads(row["source_node_ids"]) if row["source_node_ids"] else [],
                            suggested_modules=json.loads(row["suggested_modules"]) if row["suggested_modules"] else [],
                            suggested_next_steps=json.loads(row["suggested_next_steps"]) if row["suggested_next_steps"] else [],
                            created_at=row["created_at"]
                        )
                        self.drafts[draft.id] = draft
            logger.info(f"[SYNTHESIS_LOAD] Loaded {len(self.drafts)} project drafts.")
        except Exception as e:
            logger.error(f"[SYNTHESIS_LOAD_ERROR] {e}")

    def summarize_cluster(self, cluster: IdeaCluster) -> str:
        """
        Generates a descriptive summary of a cluster.
        """
        nodes = [knowledge_graph.nodes[nid] for nid in cluster.node_ids if nid in knowledge_graph.nodes]
        if not nodes:
            return "No content to summarize."
        
        contents = [n.description for n in nodes]
        # Professional Heuristic Summary
        summary = f"Este cluster titulado '{cluster.title}' agrupa {len(nodes)} conceptos clave. "
        summary += "Los temas principales incluyen: " + ", ".join([n.title.replace("Idea: ", "") for n in nodes[:3]]) + ". "
        summary += f"La visión general sugiere un enfoque hacia {cluster.title.lower()} con {len(nodes)} puntos de apoyo documentados."
        
        return summary

    def generate_project_draft(self, cluster: IdeaCluster) -> ProjectDraft:
        """
        Synthesizes a cluster into a structured project draft.
        """
        nodes = [knowledge_graph.nodes[nid] for nid in cluster.node_ids if nid in knowledge_graph.nodes]
        
        # 1. Title Extraction
        title = f"Proyecto: Omni-{cluster.title}"
        
        # 2. Synthesis
        summary = self.summarize_cluster(cluster)
        
        # 3. Heuristic Suggestions
        suggested_modules = [f"core-{cluster.title.lower()}", f"api-{cluster.title.lower()}", "ui-dashboard"]
        next_steps = [
            "Definir requisitos detallados.",
            "Validar arquitectura de datos con el Knowledge Graph.",
            f"Implementar prototipo funcional en 'chip-{cluster.title.lower()}'."
        ]
        
        draft = ProjectDraft(
            title=title,
            summary=summary,
            source_cluster_id=cluster.id,
            source_node_ids=cluster.node_ids,
            suggested_modules=suggested_modules,
            suggested_next_steps=next_steps
        )
        
        self.drafts[draft.id] = draft
        self._persist_draft(draft)
        
        # Log to auditor (Side effect)
        self._log_synthesis(draft)
        
        return draft

    def _persist_draft(self, draft: ProjectDraft):
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO ai_host_project_drafts 
                        (id, title, summary, source_cluster_id, source_node_ids, suggested_modules, suggested_next_steps, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        draft.id, draft.title, draft.summary, draft.source_cluster_id,
                        json.dumps(draft.source_node_ids), json.dumps(draft.suggested_modules),
                        json.dumps(draft.suggested_next_steps), draft.created_at
                    ))
                    conn.commit()
        except Exception as e:
            logger.error(f"[SYNTHESIS_PERSIST_ERROR] {e}")

    def _log_synthesis(self, draft: ProjectDraft):
        try:
            from backend.core.system_auditor.auditor import auditor
            auditor.log_entry(
                "INFO",
                f"Project Draft synthesized: {draft.title}",
                "ai-host",
                {"draft_id": draft.id, "type": "synthesis_event"}
            )
        except Exception:
            pass

    def get_drafts_by_cluster(self, cluster_id: str) -> List[ProjectDraft]:
        return [d for d in self.drafts.values() if d.source_cluster_id == cluster_id]

    def generate_evolution_report(self, project_slug: str, lineage: Any, events: List[Any]) -> EvolutionReport:
        """
        Synthesizes technical progress into a coherent, premium evolution report.
        """
        # 1. Context Retrieval
        cluster = cluster_manager.get_cluster(lineage.source_cluster_id) if lineage.source_cluster_id else None
        cluster_title = cluster.title if cluster else "Nodos Independientes"
        
        # 2. Origin Analysis
        node_count = len(lineage.source_node_ids)
        origin_summary = f"### 1. Origen del Proyecto\n"
        origin_summary += f"El proyecto **{project_slug.capitalize()}** tiene su génesis en el cluster de ideas **'{cluster_title}'**. "
        origin_summary += f"Se destilaron {node_count} conceptos clave del Knowledge Graph para formar la base conceptual.\n"

        # 3. Initialization State
        init_events = [e for e in lineage.related_events if e.get("type") == "initialized"]
        init_date = time.ctime(lineage.created_at)
        structure_summary = f"### 2. Estructura Inicial\n"
        structure_summary += f"Inicializado formalmente el **{init_date}**. "
        structure_summary += "Se generó un scaffold premium que incluye capas de /core, /frontend y /shared, junto con metadatos de integración (chip.json).\n"

        # 4. Technical Evolution (Activity)
        mod_events = [e for e in events if e.event_type == "MODIFIED"]
        recent_mods = mod_events[:5] # Last 5 mods
        
        activity_summary = f"### 3. Cambios Técnicos Recientes\n"
        if mod_events:
            activity_summary += f"Se han detectado **{len(mod_events)}** modificaciones técnicas desde el último hito. "
            activity_summary += "Archivos clave impactados:\n"
            for e in recent_mods:
                activity_summary += f"- `{e.file_path}`: {e.summary}\n"
        else:
            activity_summary += "No se han detectado cambios manuales en el código fuente tras la inicialización.\n"

        # 5. Inferred Status
        status = "ACTIVO" if len(mod_events) > 0 else "INICIALIZADO"
        progress_percentage = min(15 + (len(mod_events) * 5), 95) # Heuristic progress
        
        status_summary = f"### 4. Estado Actual\n"
        status_summary += f"**Estatus:** {status}\n"
        status_summary += f"**Progreso Estimado:** {progress_percentage}%\n"
        status_summary += f"El sistema infiere que el proyecto se encuentra en una fase de '{'implementación de lógica base' if status == 'ACTIVO' else 'configuración de arquitectura'}'.\n"

        # 6. Next Steps
        suggested_next_steps = [
            "Validar la integridad de los archivos modificados recientemente contra el README original.",
            "Expandir la documentación técnica en el Knowledge Graph sobre los nuevos módulos.",
            "Ejecutar un 'Self-Audit' del sistema para asegurar que no se introdujo deuda técnica."
        ]
        if status == "INICIALIZADO":
            suggested_next_steps.insert(0, "Comenzar la implementación de la lógica principal en `core/main.py`.")

        full_summary = f"{origin_summary}\n{structure_summary}\n{activity_summary}\n{status_summary}"

        report = EvolutionReport(
            project_slug=project_slug,
            title=f"Reporte de Evolución Técnica: {project_slug.capitalize()}",
            summary=full_summary,
            source_cluster_id=lineage.source_cluster_id,
            source_node_ids=lineage.source_node_ids,
            lineage_ids=[lineage.id],
            activity_event_ids=[e.id for e in events if hasattr(e, 'id')],
            suggested_next_steps=suggested_next_steps
        )
        
        self.reports[report.id] = report
        self._persist_report(report)
        return report

    def _persist_report(self, report: EvolutionReport):
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO ai_host_evolution_reports 
                        (id, project_slug, title, summary, source_cluster_id, source_node_ids, lineage_ids, activity_event_ids, suggested_next_steps, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        report.id, report.project_slug, report.title, report.summary,
                        report.source_cluster_id, json.dumps(report.source_node_ids),
                        json.dumps(report.lineage_ids), json.dumps(report.activity_event_ids),
                        json.dumps(report.suggested_next_steps), report.created_at
                    ))
                    conn.commit()
        except Exception as e:
            logger.error(f"[REPORTS_PERSIST_ERROR] {e}")

synthesis_engine = SynthesisEngine()
