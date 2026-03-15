import logging
import time
from typing import Dict, Any, Optional, List
from .idea_capture import idea_capture
from .knowledge_graph import knowledge_graph
from .cluster_manager import cluster_manager
from ..synthesis.synthesis_engine import synthesis_engine
from .project_manager import project_manager
from ..monitoring.project_watcher import project_watcher
from ..processors.base import AICommandResponse
from ..routing.utils import extract_memory_query

logger = logging.getLogger(__name__)

class MemoryRouter:
    """
    Orchestrates memory-related intents and directs them to the correct 
    storage or retrieval sub-system.
    """
    
    async def _resolve_project(self, name: str):
        """
        Helper to find a project by slug or partial match.
        Returns (slug, lineage) or (None, None).
        """
        slug = name.lower().replace(" ", "-")
        lineage = project_manager.get_lineage(slug)
        
        if not lineage and name:
            # Fallback search
            for lin in project_manager.lineages.values():
                if name.lower() in lin.project_slug.lower():
                    lineage = lin
                    slug = lin.project_slug
                    break
        return slug, lineage

    async def route_memory_task(self, intent: str, msg: str, context: Optional[Dict[str, Any]] = None) -> Optional[AICommandResponse]:
        """
        Main entry point for memory orchestration.
        """
        logger.info(f"[MEMORY_ROUTER] Handling intent: {intent}")
        
        if intent == "idea_captured":
            return await self._handle_capture(msg)
        elif intent == "list_ideas":
            return await self._handle_list_ideas()
        elif intent == "search_knowledge":
            # Extract query using utils
            query = extract_memory_query(msg)
            return await self._handle_search(query)
        elif intent == "list_clusters":
            return await self._handle_list_clusters()
        elif intent == "show_cluster":
            # Extract cluster name
            query = extract_memory_query(msg)
            return await self._handle_show_cluster(query)
        elif intent == "group_ideas":
            return await self._handle_group_ideas()
        elif intent == "summarize_cluster":
            query = extract_memory_query(msg)
            return await self._handle_summarize_cluster(query)
        elif intent == "generate_project_draft":
            query = extract_memory_query(msg)
            return await self._handle_generate_draft(query)
        elif intent == "initialize_project":
            query = extract_memory_query(msg)
            return await self._handle_initialize_project(query)
        elif intent == "show_project_evolution":
            query = extract_memory_query(msg)
            return await self._handle_show_evolution(query)
        elif intent == "show_cluster_lineage":
            query = extract_memory_query(msg)
            return await self._handle_show_cluster_lineage(query)
        elif intent == "show_project_activity":
            query = extract_memory_query(msg)
            return await self._handle_show_activity(query)
        elif intent == "scan_projects":
            return await self._handle_scan_projects()
        elif intent == "generate_evolution_report":
            query = extract_memory_query(msg)
            return await self._handle_generate_evolution_report(query)
        elif intent == "get_project_timeline":
            query = extract_memory_query(msg)
            return await self._handle_get_timeline(query)
            
        return None

    async def _handle_get_timeline(self, name: str) -> AICommandResponse:
        # 1. Resolve Project
        slug, lineage = await self._resolve_project(name)
        
        if not lineage:
            return AICommandResponse(intent="get_project_timeline", status="error", message=f"No encontré el proyecto '{name}' para generar el timeline.")

        timeline = []

        # 2. Origin (Ideas/Clusters)
        if lineage.source_cluster_id:
            cluster = cluster_manager.get_cluster(lineage.source_cluster_id)
            if cluster:
                timeline.append({
                    "timestamp": cluster.created_at,
                    "type": "origin",
                    "title": f"Origen: {cluster.title}",
                    "description": cluster.description or f"Cluster de ideas que dio origen al proyecto.",
                    "metadata": {"cluster_id": cluster.id}
                })

        for node_id in lineage.source_node_ids:
            # Try to find if this node belongs to an idea
            node = knowledge_graph.nodes.get(node_id)
            if node:
                timeline.append({
                    "timestamp": node.created_at if hasattr(node, "created_at") else lineage.created_at - 1000,
                    "type": "idea",
                    "title": node.title,
                    "description": node.description[:100] + "...",
                    "metadata": {"node_id": node_id}
                })

        # 3. Initialization
        timeline.append({
            "timestamp": lineage.created_at,
            "type": "initialization",
            "title": "Proyecto Inicializado",
            "description": f"Se creó la estructura base del proyecto '{slug}'.",
            "metadata": {"path": f"chips/chip-{slug}"}
        })

        # 4. Activity Events
        project_watcher.scan_project(lineage)
        events = [e for e in project_watcher.events if e.project_slug == slug]
        for e in events:
            timeline.append({
                "timestamp": e.created_at,
                "type": "activity",
                "title": e.event_type,
                "description": f"Archivo: `{e.file_path}`",
                "metadata": {"event_id": e.id}
            })

        # 5. Evolution Reports
        reports = synthesis_engine.get_reports_by_project(slug)
        for r in reports:
            timeline.append({
                "timestamp": r.created_at,
                "type": "report",
                "title": "Reporte de Evolución",
                "description": r.title,
                "metadata": {"report_id": r.id}
            })

        # 6. Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])

        return AICommandResponse(
            intent="get_project_timeline",
            status="success",
            message=f"### Línea de Tiempo: {slug}\nHe generado una vista secuencial de la evolución de este proyecto.",
            payload={
                "project_slug": slug,
                "timeline": timeline,
                "status": "ACTIVO" if len(events) > 0 else "INICIALIZADO",
                "progress": min(100, 10 + len(events) * 5) # Heuristic
            }
        )

    async def _handle_generate_evolution_report(self, name: str) -> AICommandResponse:
        # 1. Resolve Project
        slug, lineage = await self._resolve_project(name)
        
        if not lineage:
            # Fallback search
            found = False
            for lin in project_manager.lineages.values():
                if name.lower() in lin.project_slug.lower():
                    lineage = lin
                    slug = lin.project_slug
                    found = True
                    break
            if not found:
                return AICommandResponse(intent="generate_evolution_report", status="error", message=f"No encontré el proyecto '{name}' para generar el reporte.")
        
        # 2. Gather Data (Fresh Scan)
        project_watcher.scan_project(lineage)
        events = [e for e in project_watcher.events if e.project_slug == slug]
        
        # 3. Call Synthesis Engine
        report = synthesis_engine.generate_evolution_report(slug, lineage, events)
        
        # 4. Format Output
        next_steps = "\n".join([f"{i+1}. {s}" for i, s in enumerate(report.suggested_next_steps)])
        msg = f"### {report.title}\n\n"
        msg += f"{report.summary}\n\n"
        msg += f"**Sugerencias de Próximos Pasos:**\n{next_steps}\n\n"
        msg += f"*Reporte generado el {time.ctime(report.created_at)}*"
        
        return AICommandResponse(
            intent="generate_evolution_report",
            status="success",
            message=msg,
            payload={"report": report.model_dump()}
        )

    async def _handle_show_activity(self, name: str) -> AICommandResponse:
        # 1. Resolve Project
        slug, lineage = await self._resolve_project(name)

        # 2. Activity scan first for fresh results
        if lineage:
            project_watcher.scan_project(lineage)
        else:
            project_watcher.scan_all_projects()
        
        # 3. Get Events
        events = project_watcher.get_recent_activity(slug if lineage else None)
        
        if not events:
            name_display = slug if slug else "Global"
            return AICommandResponse(intent="show_project_activity", status="success", message=f"No se detectó actividad reciente en '{name_display}'.")
            
        evt_list = "\n".join([f"- [{time.ctime(e.created_at)}] {e.event_type}: `{e.file_path}`" for e in events])
        msg = f"### Actividad Reciente: {slug if slug else 'Global'}\n\n{evt_list}"
        
        return AICommandResponse(
            intent="show_project_activity",
            status="success",
            message=msg,
            payload={"events": [e.model_dump() for e in events]}
        )

    async def _handle_scan_projects(self) -> AICommandResponse:
        new_events = project_watcher.scan_all_projects()
        count = len(new_events)
        
        if count == 0:
            return AICommandResponse(intent="scan_projects", status="success", message="Escaneo completado. No se detectaron cambios nuevos en los proyectos.")
            
        return AICommandResponse(
            intent="scan_projects",
            status="success",
            message=f"Escaneo completado. Se detectaron {count} cambios nuevos en los proyectos.",
            payload={"new_events": [e.model_dump() for e in new_events]}
        )

    async def _handle_show_evolution(self, name: str) -> AICommandResponse:
        # 1. Resolve Project
        slug, lineage = await self._resolve_project(name)
        
        if not lineage:
            return AICommandResponse(intent="show_project_evolution", status="error", message=f"No encontré registros de evolución para el proyecto '{name}'.")
            
        events = "\n".join([f"- [{time.ctime(e['timestamp'])}] {e['type'].upper()}: {e['message']}" for e in lineage.related_events])
        msg = f"### Evolución del Proyecto: {lineage.project_slug}\n"
        msg += f"**Iniciado:** {time.ctime(lineage.created_at)}\n"
        msg += f"**Última actualización:** {time.ctime(lineage.updated_at)}\n\n"
        msg += f"**Eventos:**\n{events}"
        
        return AICommandResponse(
            intent="show_project_evolution",
            status="success",
            message=msg,
            payload={"lineage": lineage.model_dump()}
        )

    async def _handle_show_cluster_lineage(self, name: str) -> AICommandResponse:
        cluster = cluster_manager.get_cluster_by_title(name)
        if not cluster:
            return AICommandResponse(intent="show_cluster_lineage", status="error", message=f"Cluster '{name}' no encontrado.")
            
        # Find all lineages pointing to this cluster
        related_projects = [lin for lin in project_manager.lineages.values() if lin.source_cluster_id == cluster.id]
        
        if not related_projects:
            return AICommandResponse(intent="show_cluster_lineage", status="success", message=f"No hay proyectos físicos vinculados aún al cluster '{cluster.title}'.")
            
        proj_list = "\n".join([f"- **{p.project_slug}** (Iniciado: {time.ctime(p.created_at)})" for p in related_projects])
        msg = f"### Proyectos derivados del cluster: {cluster.title}\n"
        msg += f"He identificado {len(related_projects)} proyecto(s) derivado(s) de estas ideas:\n\n{proj_list}"
        
        return AICommandResponse(
            intent="show_cluster_lineage",
            status="success",
            message=msg,
            payload={"projects": [p.model_dump() for p in related_projects]}
        )

    async def _handle_initialize_project(self, name: str) -> AICommandResponse:
        cluster = cluster_manager.get_cluster_by_title(name)
        if not cluster:
            return AICommandResponse(intent="initialize_project", status="error", message=f"No encontré el cluster '{name}' para inicializar el proyecto.")
            
        # Check if we have a draft for it
        drafts = synthesis_engine.get_drafts_by_cluster(cluster.id)
        if not drafts:
            return AICommandResponse(intent="initialize_project", status="error", message=f"No hay un borrador de proyecto generado para el cluster '{cluster.title}'. Generá uno primero con 'generá un borrador de proyecto sobre {name}'.")
            
        draft = drafts[0] # Use the latest/first draft
        result = project_manager.initialize_project(draft)
        
        if result["status"] == "success":
            return AICommandResponse(
                intent="initialize_project",
                status="success",
                message=result["message"],
                payload={
                    "project_path": result["path"],
                    "project_slug": result.get("project_slug"),
                    "lineage": result.get("lineage")
                }
            )
        else:
            return AICommandResponse(intent="initialize_project", status="error", message=result["message"])

    async def _handle_summarize_cluster(self, name: str) -> AICommandResponse:
        cluster = cluster_manager.get_cluster_by_title(name)
        if not cluster:
            return AICommandResponse(intent="summarize_cluster", status="error", message=f"Cluster '{name}' not found for summary.")
            
        summary = synthesis_engine.summarize_cluster(cluster)
        return AICommandResponse(
            intent="summarize_cluster",
            status="success",
            message=f"### Resumen del Cluster: {cluster.title}\n\n{summary}",
            payload={"cluster_id": cluster.id, "summary": summary}
        )

    async def _handle_generate_draft(self, name: str) -> AICommandResponse:
        cluster = cluster_manager.get_cluster_by_title(name)
        if not cluster:
            # If no specific cluster mentioned, attempt to use the last updated one? 
            # For now, require name.
            return AICommandResponse(intent="generate_project_draft", status="error", message=f"Para generar un borrador, necesito identificar un cluster. No encontré '{name}'.")
            
        draft = synthesis_engine.generate_project_draft(cluster)
        
        # Format nice response
        msg = f"### {draft.title}\n\n"
        msg += f"**Resumen Ejecutivo:**\n{draft.summary}\n\n"
        msg += "**Módulos Sugeridos:**\n" + "\n".join([f"- `{m}`" for m in draft.suggested_modules]) + "\n\n"
        msg += "**Próximos Pasos:**\n" + "\n".join([f"1. {s}" for s in draft.suggested_next_steps])
        msg += f"\n\n*(Borrador persistido con ID: {draft.id[:8]})*"

        return AICommandResponse(
            intent="generate_project_draft",
            status="success",
            message=msg,
            payload={"draft": draft.model_dump()}
        )

    async def _handle_list_clusters(self) -> AICommandResponse:
        clusters = cluster_manager.get_all_clusters()
        if not clusters:
            return AICommandResponse(intent="list_clusters", status="success", message="No clusters detected yet. Use 'agrupar ideas' to run detection.")
            
        cluster_list = "\n".join([f"- {c.title}: {c.description} ({len(c.node_ids)} nodes)" for c in clusters])
        return AICommandResponse(
            intent="list_clusters",
            status="success",
            message=f"I found {len(clusters)} semantic clusters:\n\n{cluster_list}",
            payload={"clusters": [c.model_dump() for c in clusters]}
        )

    async def _handle_show_cluster(self, name: str) -> AICommandResponse:
        cluster = cluster_manager.get_cluster_by_title(name)
        if not cluster:
            return AICommandResponse(intent="show_cluster", status="error", message=f"Cluster '{name}' not found.")
            
        # Get nodes data
        nodes = []
        for nid in cluster.node_ids:
            if nid in knowledge_graph.nodes:
                nodes.append(knowledge_graph.nodes[nid])
        
        node_list = "\n".join([f"- {n.title}: {n.description[:100]}..." for n in nodes])
        return AICommandResponse(
            intent="show_cluster",
            status="success",
            message=f"### Cluster: {cluster.title}\n{cluster.description}\n\n**Nodes in this cluster:**\n{node_list}",
            payload={"cluster": cluster.model_dump(), "nodes": [n.model_dump() for n in nodes]}
        )

    async def _handle_group_ideas(self) -> AICommandResponse:
        new_clusters = cluster_manager.auto_group_ideas()
        count = len(new_clusters)
        
        if count == 0:
            return AICommandResponse(intent="group_ideas", status="success", message="Idea grouping complete. No new clusters found, but existing ones have been updated.")
            
        titles = ", ".join([c.title for c in new_clusters])
        return AICommandResponse(
            intent="group_ideas",
            status="success",
            message=f"Success! I detected {count} new clusters: {titles}.",
            payload={"new_clusters": [c.model_dump() for c in new_clusters]}
        )

    async def _handle_capture(self, msg: str) -> AICommandResponse:
        # Clean the message to extract only the idea content
        idea_text = msg.strip()
        if not idea_text:
            return AICommandResponse(intent="idea_captured", status="error", message="The idea content is empty.")
            
        # Extract tags if any (basic heuristic)
        tags = []
        if " con el tag " in idea_text:
            parts = idea_text.split(" con el tag ")
            idea_text = parts[0]
            tags = [t.strip() for t in parts[1].split(",")]
        elif " with tag " in idea_text:
            parts = idea_text.split(" with tag ")
            idea_text = parts[0]
            tags = [t.strip() for t in parts[1].split(",")]
            
        idea = idea_capture.capture_idea(idea_text, tags=tags)
        
        return AICommandResponse(
            intent="idea_captured",
            status="success",
            message=f"Idea captured and stored in Knowledge Base. (Ref: {idea.id[:8]})",
            payload={
                "idea_id": idea.id,
                "timestamp": idea.timestamp,
                "related_nodes": idea.related_nodes
            }
        )

    async def _handle_list_ideas(self) -> AICommandResponse:
        ideas = idea_capture.get_all_ideas()
        if not ideas:
            return AICommandResponse(intent="list_ideas", status="success", message="You haven't captured any ideas yet.")
            
        idea_list = "\n".join([f"- {i.content[:60]}... (ID: {i.id[:8]})" for i in ideas])
        return AICommandResponse(
            intent="list_ideas",
            status="success",
            message=f"I found {len(ideas)} captured thoughts:\n\n{idea_list}",
            payload={"ideas": [i.model_dump() for i in ideas]}
        )

    async def _handle_search(self, query: str) -> AICommandResponse:
        # Simple extraction of query
        nodes = knowledge_graph.search_knowledge(query)
        ideas = idea_capture.search_ideas(query)
        
        count = len(nodes) + len(ideas)
        if count == 0:
            return AICommandResponse(intent="search_knowledge", status="success", message=f"No results found for '{query}'.")

        msg = f"Memory Search Results ({count} items):\n"
        if ideas:
            msg += "\nIdeas:\n" + "\n".join([f"- {i.content[:50]}..." for i in ideas])
        if nodes:
            msg += "\nKnowledge Nodes:\n" + "\n".join([f"- {n.title}: {n.description[:50]}..." for n in nodes])

        return AICommandResponse(
            intent="search_knowledge",
            status="success",
            message=msg,
            payload={
                "ideas": [i.model_dump() for i in ideas],
                "nodes": [n.model_dump() for n in nodes]
            }
        )

memory_router = MemoryRouter()
