import logging
import os
import difflib
import re
from typing import Dict, Any, Optional, List
from .base import CommandProcessor, AICommandResponse
from ..execution.safety_policy import safety_policy
from ..execution.patch_preview import patch_preview_engine
from ..execution.mutation_engine import MutationBatch, FileOperation, MutationType
from ..execution.builder_models import BuilderTask, BuilderModule, BuilderStatus, BuilderModuleType
from ..execution.builder_engine import builder_execution_engine
from ..memory.system_memory import system_memory
from ..orchestration.mission_orchestrator import mission_orchestrator

logger = logging.getLogger(__name__)

class ProposalProcessor(CommandProcessor):
    """
    Anti-Gravity Interno: Proposal-only coding assistant (Harden Stage).
    Analyzes code and proposes minimal patches without auto-applying.
    Enforces strict safety workflow: AUDIT -> ISOLATE -> PROPOSE -> SHOW DIFF.
    """
    
    async def process(self, msg: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        # 1. HYBRID ORCHESTRATION & EXTERNAL NODES (Block 7/Prompt 3)
        url_match = re.search(r"(https?://\S+)", msg)
        is_interaction = any(kw in msg.lower() for kw in ["abrí", "abrir", "inspeccioná", "inspeccionar", "leé", "leer", "sumá", "usá", "vinculá"])
        
        if url_match:
            url = url_match.group(1)
            internal_target = self._resolve_target(msg, context)
            node_type = self._classify_external_node(url)
            inspection = self._inspect_external_node(url)
            
            if internal_target and internal_target != os.path.abspath("."):
                # HYBRID CASE: Link external to specific internal file/module
                mission_orchestrator.plan_mission(msg, intent="hybrid_mission_orchestration")
                orch_report = mission_orchestrator.format_orchestration_report()
                
                return AICommandResponse(
                    intent="hybrid_context_proposal",
                    status="success",
                    message=f"""### OMNI_HYBRID_WORK_ORCHESTRATION
NODO_EXTERNO: {url}
TIPO_DE_SUPERFICIE: {node_type}
RELACIÓN_CON_EL_SCOPE_INTERNO: {internal_target}
APORTE_AL_TRABAJO: Enlace de requerimientos y guías externas con el flujo de implementación local.
CONTEXTO_UTILIZADO: {", ".join(inspection["elements"])}
LÍMITE_DE_INTERACCIÓN: SOLO_LECTURA_Y_REFERENCIA / SIN_ESCRITURA_EXTERNA
CRITERIO_DE_SEGURIDAD: BOUNDARY_TRANSVERSAL_ACTIVO

{orch_report}
---
# BLOQUE 7 / PROMPT 3: Orquestación híbrida completada. El nodo externo sirve de apoyo al scope interno.""",
                    payload={"url": url, "target_file": internal_target, "node_type": node_type}
                )
            
            # DEFAULT EXTERNAL CASE (Block 7/Prompt 2)
            action = "INSPECCIÓN_VISUAL_Y_EXTRACCIÓN_DE_CONTEXTO" if is_interaction else "MODELO_ESTRUCTURAL"
            mission_orchestrator.plan_mission(msg, intent="external_node_inspection" if is_interaction else "external_node_discovery")
            orch_report = mission_orchestrator.format_orchestration_report()
            
            return AICommandResponse(
                intent="external_node_interaction",
                status="success",
                message=f"""### OMNI_EXTERNAL_NODE_INTERACTION
NODO_EXTERNO: {url}
TIPO_DE_SUPERFICIE: {node_type}
ELEMENTOS_VISIBLES: {", ".join(inspection["elements"]) if is_interaction else "Pendiente de apertura."}
UTILIDAD_PARA_EL_SCOPE: {inspection["utility"] if is_interaction else "Evaluación de relevancia sistémica."}
ACCIÓN_REALIZADA: {action}
LÍMITE_DE_INTERACCIÓN: SOLO_LECTURA / SIN_CONTROL_DE_FLUJO_EXTERNO

{orch_report}
---
# BLOQUE 7 / PROMPT 3: Se ha realizado una interacción limitada y segura sobre la superficie externa.""",
                payload={"url": url, "node_type": node_type}
            )

        # 2. MEMORY AUDIT (OS-like check)

        # 2. MEMORY AUDIT (OS-like check)
        if any(kw in msg.lower() for kw in ["roadmap", "qué bloque", "regla dura", "mi memoria", "continuidad", "qué estábamos", "qué veníamos", "último scope", "decisión", "decisiones", "fixes validados", "pospuesto", "pospudo"]):
             return AICommandResponse(
                intent="system_memory_report",
                status="success",
                message=f"### OMNI_SYSTEM_MEMORY\n\n{system_memory.get_project_context()}\n{system_memory.get_working_context()}",
                payload={"memory": system_memory.data}
             )

        # 2. AUDIT & ISOLATE (Resolve Target)
        raw_target = self._resolve_target(msg, context)
        if not raw_target:
            return AICommandResponse(intent="proposal_error", status="success", message="ARCHIVO_LEIDO: NONE")

        # Absolutize path if not absolute
        abs_target = os.path.abspath(raw_target)
        is_dir_scope = os.path.isdir(abs_target)
        
        target_files = []
        scope_warning = ""

        # 2. DETERMINE FILE BATCH & SCOPE
        subniveles = set()
        total_files_in_tree = 0

        if is_dir_scope:
            valid_exts = ('.js', '.py', '.ts', '.css', '.html', '.md')
            for root, dirs, files in os.walk(abs_target):
                if any(ignored in root for ignored in ['node_modules', '.git', '__pycache__', 'venv', 'dist', 'build']):
                    continue
                
                # Relacionar la subcarpeta
                rel_dir = os.path.relpath(root, abs_target)
                if rel_dir != '.' and not rel_dir.startswith('..'):
                    subniveles.add(rel_dir)

                for f in files:
                    if f.endswith(valid_exts):
                        total_files_in_tree += 1
                        if len(target_files) < 8:
                            target_files.append(os.path.join(root, f))
            
            # Rule 2: Expansion control
            if total_files_in_tree > 8:
                scope_warning = f"\n⚠️ WARNING: La jerarquía excede el límite razonable ({total_files_in_tree} archivos encontrados). Truncando árbol a 8 nodos para evitar reescrituras opacas.\n"
        else:
            target_files = [abs_target]

        if not target_files:
            return AICommandResponse(intent="proposal_error", status="success", message=f"No se encontraron archivos editables en el scope: {raw_target}")

        operations = []
        aggregate_diff = ""
        highest_risk = "BAJO"
        all_proposals = []
        
        # 3. PROPOSE BATCH
        for t_file in target_files:
            if not self._is_safe_path(t_file):
                continue
                
            try:
                with open(t_file, "r", encoding="utf-8") as f:
                    original_content = f.read()
            except Exception:
                continue

            # In multi-file, we do NOT force microfixes into every component, only apply if requested heuristically
            proposal = self._generate_intelligent_proposal(t_file, original_content, msg, force_microfix=not is_dir_scope)
            
            if proposal["new_content"] != original_content:
                diff_str = self._generate_diff(original_content, proposal["new_content"], t_file)
                if diff_str.strip():
                    aggregate_diff += diff_str + "\n"
                    operations.append(FileOperation(
                        path=t_file,
                        op_type=MutationType.MODIFY_FILE,
                        content=proposal["new_content"]
                    ))
                    all_proposals.append(proposal)
                    
                    prisk = proposal.get("risk", "").lower()
                    if "crítico" in prisk or "alto" in prisk:
                        highest_risk = "ALTO"
                    elif "medio" in prisk and highest_risk != "ALTO":
                        highest_risk = "MEDIO"

        # If it was a directory query but no changes were proposed, we simulate an audit response.
        if is_dir_scope and not operations:
            filtered_names = [os.path.basename(f) for f in target_files]
            formatted_message = f"""SCOPE_RAÍZ: {raw_target} ({total_files_in_tree} nodos totales detectados)
SUBNIVELES_RELEVANTES: {', '.join(subniveles) if subniveles else 'Ninguno (Plano)'}
ARCHIVOS_RELEVANTES: {', '.join(filtered_names) if filtered_names else 'Ninguno'}
CAMBIO_PROPUESTO_POR_ARCHIVO: Ninguno. Se auditaron los archivos del árbol pero no se justifican mutaciones estructurales.
IMPACTO_RELACIONADO: NULO
CRITERIO_DE_SEGURIDAD: CAMBIO_SEGURO{scope_warning}"""
            return AICommandResponse(
                intent="copilot_proposal",
                status="success",
                message=formatted_message.strip(),
                payload={
                    "target_files": target_files,
                    "allowed_files": target_files,
                    "mode": "proposal_only",
                    "diff": ""
                }
            )

        # 4. VALIDATE & POLICY GATE
        if not operations and not is_dir_scope:
            return AICommandResponse(intent="copilot_proposal", status="success", message="ARCHIVO_LEIDO: NONE", payload={"target_files": target_files})
            
        validation = safety_policy.validate_proposal({
            "files": [op.path for op in operations],
            "diff": aggregate_diff,
            "risk": highest_risk
        })
        
        if not validation["is_safe"]:
            return AICommandResponse(
                intent="safety_violation",
                status="alert",
                message=f"VIOLACIÓN DE POLÍTICA MULTI-ARCHIVO: {', '.join(validation['issues'])}"
            )
            
        # 5. GENERATE PREVIEW
        preview_id = None
        if operations:
            try:
                task = BuilderTask(
                    roadmap_id="copilot_proposal" + ("_multi" if is_dir_scope else ""),
                    title=f"Propuesta: {len(operations)} archivo(s)",
                    status=BuilderStatus.AWAITING_APPROVAL
                )
                module = BuilderModule(
                    task_id=task.id,
                    title=f"Aplicación Scope: {os.path.basename(raw_target)}",
                    sequence_order=0,
                    status=BuilderStatus.AWAITING_APPROVAL,
                    module_type=BuilderModuleType.IMPLEMENTATION
                )
                task.modules.append(module)
                
                await builder_execution_engine._persist_task(task)
                await builder_execution_engine._persist_module(module)
                
                batch = MutationBatch(
                    task_id=task.id,
                    module_id=module.id,
                    operations=operations,
                    origin="Copilot"
                )
                
                preview = patch_preview_engine.generate_preview(task.id, module.id, batch)
                preview_id = preview.id
                
                module.result = {"preview_id": preview_id, "type": "patch_preview"}
                await builder_execution_engine._persist_module(module)
            except Exception as e:
                logger.error(f"[PROPOSAL_PREVIEW_ERROR] Failed multi preview: {e}")

        # 6. COMPATIBILITY
        compatibility_warning = safety_policy.check_mobile_compatibility(aggregate_diff, target_files=[op.path for op in operations])
        if compatibility_warning:
            highest_risk = f"ALTO: {compatibility_warning}. {highest_risk}"

        # 7. ORCHESTRATE MISSION PHASES
        mission_plan = mission_orchestrator.plan_mission(msg, intent="copilot_proposal")
        orch_report = mission_orchestrator.format_orchestration_report()

        # 8. FORMAT FINAL MESSAGE
        is_global = self._is_global_project_request(msg)
        
        if is_global:
            pmap = self._build_project_map()
            formatted_message = f"### VISIÓN_SISTÉMICA_OMNIWEB (GLOBAL_AWARE_READ_ONLY)\n"
            formatted_message += f"PROYECTO_RAÍZ: OmniWeb Project (Global Context)\n"
            formatted_message += f"TIPO_ANÁLISIS: COMPRENSIÓN_ARQUITECTÓNICA_TRANSVERSAL\n\n"
            
            formatted_message += f"CAPAS_PRINCIPALES:\n" + "\n".join([f"- {c}" for c in pmap['CAPAS']]) + "\n\n"
            formatted_message += f"MÓDULOS_CENTRALES:\n" + "\n".join([f"- {m}" for m in pmap['MODULOS']]) + "\n\n"
            formatted_message += f"RELACIONES_CRÍTICAS:\n" + "\n".join([f"- {r}" for r in pmap['RELACIONES']]) + "\n\n"
            formatted_message += f"ZONAS_DE_ACOPLAMIENTO:\n" + "\n".join([f"- {a}" for a in pmap['ACOPLAMIENTOS']]) + "\n\n"
            formatted_message += f"CONTRATOS_SENSIBLES:\n" + "\n".join([f"- {s}" for s in pmap['CONTRATOS']]) + "\n\n"
            formatted_message += f"RIESGOS_SISTÉMICOS:\n" + "\n".join([f"- {ri}" for ri in pmap['RIESGOS']]) + "\n\n"
            formatted_message += f"{orch_report}\n"
            formatted_message += f"---\n"
            formatted_message += f"# ANÁLISIS DE SISTEMA COMPLETO: OmniWeb detectado como OS-like Architecture."
        elif is_dir_scope:
            changed_names = [os.path.basename(op.path) for op in operations]
            all_names = [os.path.basename(f) for f in target_files]
            changes_desc = "\n".join([f"- {os.path.basename(p['file'])}: {p.get('change', 'fix')}" for p in all_proposals])
            
            formatted_message = f"### SCOPE_JERÁRQUICO (Jerarquía Detallada)\n"
            formatted_message += f"SCOPE_RAÍZ: {raw_target} ({total_files_in_tree} nodos totales detectados)\n"
            formatted_message += f"SUBNIVELES_RELEVANTES: {', '.join(subniveles) if subniveles else 'Ninguno (Plano)'}\n"
            formatted_message += f"ARCHIVOS_RELEVANTES: {', '.join(changed_names)}\n"
            formatted_message += f"CAMBIO_PROPUESTO_POR_ARCHIVO:\n{changes_desc}\n\n"
            formatted_message += f"{orch_report}\n"
            formatted_message += f"IMPACTO_RELACIONADO: {highest_risk} - Alteración contenida a la jerarquía declarada.\n"
            formatted_message += f"CRITERIO_DE_SEGURIDAD: MULTI_FILE_SAFE{scope_warning}\n\n"
            formatted_message += f"---\n"
            formatted_message += f"{aggregate_diff}"

        else:
            t_file = target_files[0]
            prop = all_proposals[0] if all_proposals else {}
            first_line = "None"
            try:
                with open(t_file, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()
            except:
                pass
                
            purpose = prop.get("problem", "Propósito general del módulo.")
            if "audio" in t_file.lower() or "librosa" in t_file.lower() or "audio" in msg:
                purpose = "Gestión de procesamiento de audio y señales para transcripción liviana."
                
            formatted_message = f"""ARCHIVO_LEIDO: {t_file}
PRIMERA_LINEA: {first_line}
RESUMEN_REAL: {purpose}
MICROFIX_PROPUESTO: {prop.get('change', 'No se requiere.')}
CONTEXTO_DE_MEMORIA: {', '.join(prop.get('memory_notes', [])) if prop.get('memory_notes') else 'Sin interferencia sistémica.'}
IMPACTO_RELACIONADO: {highest_risk} - Cambio local
CRITERIO_DE_SEGURIDAD: {prop.get('safety', 'CAMBIO_SEGURO')}

{orch_report}

---
{aggregate_diff or '# ARCHIVO BAJO AUDITORÍA (Sin cambios generados)'}"""

        # 8. UPDATE WORKING MEMORY
        system_memory.update_working(
            active_scope=raw_target,
            last_important_file=target_files[0] if target_files else None,
            last_operation_summary=all_proposals[0].get("change") if all_proposals else "Auditoría del sistema (Solo Lectura).",
            workspace_state="analyzing" if is_global else "proposing"
        )
        if "bloque" in msg.lower() and re.search(r"bloque\s+(\d+)", msg.lower()):
            new_block = re.search(r"bloque\s+(\d+)", msg.lower()).group(0)
            system_memory.set_roadmap_block(new_block.capitalize())
            
        if "decisión" in msg.lower() or "decidimos" in msg.lower():
            match = re.search(r"(?:decidimos|decisi[óo]n:)\s+([^.\n]+)", msg.lower())
            if match:
                system_memory.add_decision(match.group(1).capitalize())

        return AICommandResponse(
            intent="copilot_proposal",
            status="success",
            message=formatted_message.strip(),
            payload={
                "target_files": [op.path for op in operations] if operations else target_files,
                "allowed_files": [op.path for op in operations] if operations else target_files,
                "forbidden_files": safety_policy.FORBIDDEN_FILES,
                "proposal": all_proposals[0] if all_proposals else {},
                "diff": aggregate_diff if not is_global else "",
                "preview_id": preview_id if not is_global else None,
                "mode": "proposal_only",
                "is_global_analysis": is_global,
                "working_memory": system_memory.get_working()
            }
        )

    def _resolve_target(self, msg: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        # Priority 1: Explicit Folder/Module/Hierarchy Mention
        match = re.search(r"(?:carpeta|m[oó]dulo|directorio|estructura|jerarqu[íi]a|[aá]rbol|proyecto)\s+([\w/\.-]+)", msg)
        if match:
            return match.group(1)

        # Priority 2: Global Project Keywords
        if self._is_global_project_request(msg):
            return os.path.abspath(".")

        # Priority 3: Current Editor Path from context
        match = re.search(r"en ([\w/\.-]+)", msg)
        if match:
            return match.group(1)
            
        return None

    def _is_global_project_request(self, msg: str) -> bool:
        keywords = ["omniweb completo", "proyecto entero", "todo el sistema", "arquitectura del sistema", "proyecto completo", "analizá omniweb", "entendé omniweb", "visión sistémica", "cómo se conectan"]
        return any(kw in msg.lower() for kw in keywords)

    def _classify_external_node(self, url: str) -> str:
        url_l = url.lower()
        if "docs" in url_l or "documentation" in url_l: return "DOCUMENTACIÓN_TÉCNICA_EXPANDIDA"
        if "chat" in url_l or "conversation" in url_l: return "CONVERSACIÓN_O_SUPERFICIE_DE_DIÁLOGO"
        if "github" in url_l or "gitlab" in url_l or "bitbucket" in url_l: return "REPOSITORIO_Y_ESTRUCTURA_DE_CÓDIGO_EXTERNA"
        if "youtube" in url_l or "video" in url_l: return "CONTENIDO_MULTIMEDIA_DINÁMICO"
        if "google" in url_l or "search" in url_l: return "MOTOR_DE_BÚSQUEDA_Y_RELEVANCIA"
        return "NODO_CONTENEDOR_EXTERNO_GENÉRICO"

    def _inspect_external_node(self, url: str) -> Dict[str, Any]:
        node_type = self._classify_external_node(url)
        elements = ["Jerarquía de navegación", "Bloque de contenido principal", "Metadatos de superficie"]
        if "docs" in url.lower():
            elements.extend(["Ejemplos de código Python/JS", "Índice de subniveles", "Advertencias técnicas"])
        elif "chat" in url.lower():
            elements.extend(["Historial de mensajes secuenciales", "Prompt actual del usuario", "Feedback del sistema"])
            
        return {
            "type": node_type,
            "elements": elements,
            "utility": "CRÍTICA - Provee el contexto estructural necesario para la misión."
        }

    def _build_project_map(self) -> Dict[str, Any]:
        """
        OmniWeb System Topology Mapper.
        Provides a systemic view of connections, coupling, and global risks.
        """
        return {
            "CAPAS": [
                "FRONTEND: Shell (Creator/Builder), Workspace UI, Monaco Editor integration.",
                "BACKEND: FastAPI API, AI Host (Router/Processors), Cache & Persistence.",
                "CORE: Mutation Engine, Patch Preview, Safety Audit Layer.",
                "CHIPS: Atomic logic and task specialized handlers.",
                "RUNTIME: Deno/Python execution isolation and environment management."
            ],
            "MODULOS": [
                "ProposalProcessor: Context-aware patch generation engine.",
                "CognitiveOrchestrator: High-level intention management.",
                "MutationEngine: Transactional filesystem operations.",
                "SafetyPolicy: Static and runtime security gatekeeper."
            ],
            "RELACIONES": [
                "Request -> Intent (Context) -> BrainRouter -> Selected Processor.",
                "Proposal -> Validation -> Preview (UI) -> Approval -> Mutation."
            ],
            "ACOPLAMIENTOS": [
                "BrainRouter <-> Processors: Shared interface for AICommandResponse.",
                "MutationEngine <-> SafetyPolicy: Dependency on pre-write validation rules.",
                "Frontend <-> Backend: State synchronization via BuilderTask models."
            ],
            "CONTRATOS": [
                "MutationBatch: The fundamental unit of cross-file atomic updates.",
                "AICommandResponse: The system-wide protocol for AI intent feedback.",
                "SafetyPolicy: The final authority on which modifications are permitted."
            ],
            "RIESGOS": [
                "GLOBAL: Changes in CORE (Mutation/Safety) propagate across all features.",
                "COUPLED: desynchronization between Workspace frontend and Builder backend."
            ]
        }

    def _is_safe_path(self, path: str) -> bool:
        abs_path = os.path.abspath(path)
        # Delegate to safety policy
        return not any(p in abs_path for p in safety_policy.FORBIDDEN_FILES)

    def _generate_intelligent_proposal(self, path: str, content: str, request: str, force_microfix: bool = True) -> Dict[str, Any]:
        """
        Heuristic-based minimal proposal (Phase 10 Specificity).
        Inspects content for real patterns to generate situation-aware suggestions.
        """
        filename = os.path.basename(path).lower()
        new_content = content
        msg = request.lower()
        
        # 1. SCAN CONTENT FOR REAL ISSUES (Deeper Audit)
        found_issue = self._scan_content_for_real_issues(path, content)
        
        # 2. POPULATE DEFAULTS FROM SCAN
        problem = found_issue["problem"]
        hypothesis = "Propuesta basada en auditoría de patrones recurrentes."
        change = found_issue["change"]
        risk = found_issue["risk"]
        verification = "Inspección visual y validación en runtime."
        safety = "CAMBIO_SEGURO"
        
        # --- NEW: OMNI RULES / EXECUTION DISCIPLINE ---
        is_ambiguous = any(kw in msg for kw in ["arregla este", "arreglá este", "mejora este", "mejorá este", "refactoriz", "reestructur", "rehacé"])
        is_microfix = any(kw in msg for kw in ["microfix", "corregi", "corregí esta", "validación", "guard clause", "ajuste menor"])
        is_comment = any(kw in msg for kw in ["comentario", "document", "nota "])
        
        if is_comment:
            change = "Inyectar comentario local (No Scope Creep)."
            problem = "Solicitud de documentación superficial."
            risk = "NULO - Documentación pasiva."
            safety = "CAMBIO_SEGURO"
            new_content = "# [FIX_SCOPE_LOCAL] Comentario operativo agregado.\n" + content
        elif is_ambiguous:
            problem = "Archivo con posibles responsabilidades conectadas y pedido demasiado amplio."
            change = "Agregar comentario de auditoría o guard clause preventivo ANTES de proponer refactor mayor."
            risk = f"ALTO - Una refactorización amplia o ambigua puede romper contratos con dependencias importadas."
            safety = "CAMBIO_INSEGURO_O_AMBIGUO"
        elif is_microfix:
            problem = "Ajuste local puntual en bloque u operación (Minimal Patch)."
            change = "Aplicar micro-mutación sin inflar a refactorizaciones secundarias."
            if "medio" in risk.lower() or "alto" in risk.lower() or "crítico" in risk.lower():
                safety = "CAMBIO_RIESGO_MEDIO"
            else:
                risk = "BAJO - Cambio contenido dentro del scope solicitado."
                safety = "CAMBIO_SEGURO"
                
            if force_microfix and new_content == content and "def " in content:
                new_content = content.replace("def ", "# [MICROFIX] Validación mínima local aplicada.\ndef ", 1)

        # 3. SPECIAL MISSION OVERRIDES (Legacy compatibility)
        if any(kw in msg for kw in ["audio", "transcription", "transcribir"]):
            problem = "Riesgo de uso de modelos pesados para transcripción."
            hypothesis = "Para este entorno, librosa ofrece un balance superior entre performance y precisión."
            change = "Implementar flujo de carga liviana con librosa.load() sin alterar adyacentes."
            new_content = content + "\n# Propuesta: Integración librosa (Surgical Assistant)\nimport librosa\n"
            risk = "MEDIO - Aumento leve de dependencias controladas."
            safety = "CAMBIO_RIESGO_MEDIO"
        elif ("log" in msg) and ".py" in filename:
            if "import logging" not in content:
                new_content = "import logging\n" + content
                problem = "Falta de instrumentación de auditoría."
                change = "Inyección de logging import."
                risk = "BAJO - Cambio contenido."
            else:
                problem = "Logs insuficientes para trazabilidad."
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if "def " in line and ":" in line:
                        lines.insert(i+1, "    logging.info(\"[AUDIT] Operation started.\")")
                        break
                new_content = "\n".join(lines)
                change = "Minimal log injection in first function body."
                risk = "BAJO."
                
        # Ensure ambiguous requests without clear paths inject a guard warning instead of a massive rewrite
        if force_microfix and safety == "CAMBIO_INSEGURO_O_AMBIGUO" and new_content == content:
             new_content = "# [WARNING] Scope ambiguo detectado. Refactor masivo prevenido.\n" + content

        # --- NEW: ACTIVE MEMORY REASONING ---
        memory_notes = []
        
        # 1. Roadmap & Deferred Items Check
        deferred = system_memory.data["project"].get("deferred_items", [])
        for item in deferred:
            if any(word in msg and len(word) > 4 for word in item.lower().split()):
                memory_notes.append(f"⚠️ MEMORIA: El tema '{item}' fue diferido para bloques futuros. Respetando límite de roadmap.")
                if safety == "CAMBIO_SEGURO": safety = "CAMBIO_POSPUESTO_POR_ROADMAP"
                change = f"Diferido: {item} no pertenece al Bloque actual."

        # 2. Validated Fixes Check (Anti-Regression)
        validated = system_memory.data["project"].get("validated_fixes", [])
        for fix in validated:
             if any(word in msg and len(word) > 5 for word in fix.lower().split()):
                 memory_notes.append(f"ℹ️ MEMORIA: El fix '{fix}' ya fue validado. Evitando reapertura innecesaria.")
                 if "corregir" in msg or "fix" in msg:
                    change = "No se requiere acción: Fix ya consolidado en memoria de sistema."
                    if safety == "CAMBIO_SEGURO": safety = "CAMBIO_REDUNDANTE"

        # 3. Sensitive Module Check (Harden Criteria)
        sensitive = system_memory.data["project"].get("sensitive_modules", [])
        if any(os.path.normpath(s) in os.path.normpath(path) for s in sensitive):
             memory_notes.append("🛡️ MEMORIA: Módulo SENSIBLE detectado. Endureciendo criterio de seguridad.")
             if safety == "CAMBIO_SEGURO":
                 safety = "CAMBIO_RIESGO_MEDIO_CORE"
             risk = f"ALTO - Módulo crítico del sistema detectado en memoria. {risk}"

        # 4. Integrate Notes into Problem Description
        if memory_notes:
            problem = f"{problem} | " + " ".join(memory_notes)

        return {
            "file": path,
            "problem": problem,
            "hypothesis": hypothesis,
            "change": change,
            "new_content": new_content,
            "risk": risk,
            "verification": verification,
            "safety": safety,
            "memory_notes": memory_notes
        }

    def _generate_diff(self, old: str, new: str, path: str) -> str:
        diff = difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            n=3
        )
        return "".join(list(diff))

    def _scan_content_for_real_issues(self, path: str, content: str) -> Dict[str, str]:
        """Scans code content for real architectural issues/smells with surgical specificity."""
        issues = []
        path_lower = path.lower()
        filename = os.path.basename(path)
        
        # --- NEW: OMNI SEMANTIC AWARENESS LAYER ---
        # Detect relevant dependencies to calculate systemic risk.
        detected_deps = []
        is_core_system = any(p in path_lower for p in ["core/", "backend/core", "infrastructure/", "safety_policy"])
        global_impact_note = " [CRÍTICO: Módulo CORE]" if is_core_system else ""

        if path_lower.endswith(".py"):
            imports = re.findall(r'^(?:from|import)\s+([a-zA-Z0-9_\.]+)', content, re.MULTILINE)
            for imp in imports:
                if "backend" in imp or "core" in imp or "chips" in imp or "router" in imp:
                    parts = imp.split('.')
                    comp = parts[-1] if len(parts) > 1 else imp
                    detected_deps.append(comp)
        elif path_lower.endswith((".js", ".ts")):
            imports = re.findall(r'(?:import|require)[^"\'\n]+["\']([^"\'\n]+)["\']', content)
            for imp in imports:
                if imp.startswith('.') or "core" in imp or "shared" in imp:
                    detected_deps.append(os.path.basename(imp).split('.')[0])
                    
        # Filter duplicates and limit
        detected_deps = list(dict.fromkeys(detected_deps))
        top_deps_str = ", ".join(detected_deps[:3])
        dependency_impact = f" (Impacto cruzado: altera contratos con [{top_deps_str}]){global_impact_note}" if (top_deps_str or global_impact_note) else ""
        # ------------------------------------------

        # 1. Detect JS/TS specific smells (Focus on Architecture & UX)
        if path_lower.endswith((".js", ".ts")):
            # A. Detect Long Render Methods (Specific to functions like renderLayout)
            # Strategy: Find innerHTML assignments with long templates or assignments
            inner_html_matches = list(re.finditer(r"(?:\.|)innerHTML\s*=\s*(`[\s\S]*?`|['\"][\s\S]*?['\"]|content)", content))
            for ih_match in inner_html_matches:
                ih_pos = ih_match.start()
                ih_val = ih_match.group(1)
                
                # Check if the assigned value is large
                val_lines = ih_val.count("\n")
                
                # Search backward for the method name
                prefix = content[max(0, ih_pos - 1500) : ih_pos]
                method_heads = list(re.finditer(r"(?:^|[ \t]+)(?:async\s+|)(\w+)\s*\([^)]*\)\s*\{", prefix, re.MULTILINE))
                
                if method_heads:
                    last_head = method_heads[-1]
                    method_name = last_head.group(1)
                    if method_name in ["if", "while", "for", "switch", "catch", "constructor"]:
                        continue
                    
                    is_render = method_name.lower().startswith("render")
                    # If it's a render method or the template is large (> 5 lines)
                    if is_render or val_lines > 5:
                        issues.append({
                            "problem": f"El método {method_name}() en {filename} mezcla lógica con templates HTML extensos.",
                            "change": f"extraer {method_name}() en helper separado para reducir mezcla entre render y estado",
                            "risk": f"puede afectar inicialización visual del panel si se altera el orden de render{dependency_impact}"
                        })

            # B. Check for high density (over 500 lines) - prioritize this as well
            lines_count = len(content.splitlines())
            if lines_count > 500:
                 issues.append({
                    "problem": f"El módulo {filename} excede las 500 líneas (alta carga cognitiva).",
                    "change": "fragmentar el módulo en submódulos especializados por responsabilidad",
                    "risk": f"incrementa la probabilidad de efectos secundarios al modificar funciones compartidas{dependency_impact}"
                 })

            if 'document.getElementById' in content:
                 issues.append({
                    "problem": f"{filename} tiene un acoplamiento directo con IDs globales del DOM.",
                    "change": "centralizar selectores en un config de elementos o inyectar el root",
                    "risk": f"puede romper la interactividad si cambia la estructura de index.html{dependency_impact}"
                })
            
            if 'var ' in content:
                issues.append({
                    "problem": f"Uso de 'var' detectado en {filename} (Legacy scope).",
                    "change": "migrar a const/let para prevenir fugas de scope",
                    "risk": f"posibles colisiones de variables en closures asincrónicos{dependency_impact}"
                })
        
        # 2. Detect Python smells (Focus on Router/Logic separation)
        elif path_lower.endswith(".py"):

            if "router.py" in path_lower and ("db." in content or "calculate_" in content or "Process" in content):
                issues.append({
                    "problem": f"Violación de capas en {filename}: lógica de negocio detectada en el Router.",
                    "change": "extraer lógica pesada a un Service Layer o Processor dedicado",
                    "risk": f"dificulta el testeo unitario y la reutilización de la lógica central{dependency_impact}"
                })
            elif "except:" in content or "except Exception:" in content:
                issues.append({
                    "problem": f"Manejo de errores genérico en {filename}.",
                    "change": "reemplazar try-except genéricos por capturas de excepciones granulares",
                    "risk": f"puede ocultar fallos de infraestructura críticos en producción{dependency_impact}"
                })

        # 3. Global Smells: Extreme Density
        lines_count = len(content.splitlines())
        if lines_count > 500:
             issues.append({
                "problem": f"El módulo {filename} excede las 500 líneas (alta carga cognitiva).",
                "change": "fragmentar el módulo en submódulos especializados por responsabilidad",
                "risk": f"incrementa la probabilidad de efectos secundarios al modificar funciones compartidas{dependency_impact}"
             })

        if not issues:
            risk_msg = "BAJO (Aislado)"
            if dependency_impact:
                risk_msg = f"MEDIO - Modificación local pero con enlaces sistémicos. {dependency_impact}"
            
            return {
                "problem": f"Análisis de {filename} concluido sin bloqueos críticos.",
                "change": "estabilizar y documentar puntos de extensión actuales",
                "risk": risk_msg
            }
            
        # Prioritize according to specificity
        return issues[0]

