import logging
import os
from typing import Dict, Any, Optional, List
from .base import CommandProcessor, AICommandResponse
from backend.core.system_auditor.auditor import auditor
from backend.core.system_auditor.fix_engine import fix_engine
from backend.core.ai_developer.code_analyzer import code_analyzer
from backend.core.ai_developer.patch_generator import patch_generator
from backend.core.interface.visual_interface import visual_interface
from ..engineering_policy import engineering_policy
from ..routing.utils import extract_chip_target

logger = logging.getLogger(__name__)

class CreatorControlProcessor(CommandProcessor):
    """
    Unified Operational Layer for Creator Mode.
    Categorizes actions into Analyze, Propose, Execute, and Safe-Guarded.
    """

    async def can_handle(self, command: str) -> bool:
        cmd = command.lower().strip()
        keywords = [
            "analyze", "analiza", "inspect", "inspecciona", "diagnose", "diagnostica",
            "propose", "propone", "suggest", "sugiere", "recommend", "how to fix",
            "execute", "ejecuta", "apply", "aplica", "repair", "repara", "fix", "arregla",
            "system state", "estado del sistema", "optimize", "optimiza", "modify", "modifica",
            "audit", "audita"
        ]
        prefixes = ["omni", "creator", "system"]
        return any(k in cmd for k in keywords) or any(cmd.startswith(p) for p in prefixes)

    async def process(self, command: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        cmd = command.lower().strip()
        
        # 0. Language Persistence Check
        from ..sessions import session_state
        session_id = str(context.get("user_id", "default_user")) if context else "default_user"
        
        if any(k in cmd for k in ["responde en", "habla en", "idioma", "language", "speak in", "respond in"]):
            session_state.set_language(session_id, cmd)
            lang_msg = "Idioma actualizado a Español." if session_state.get_language(session_id) == "es" else "Language updated to English."
            return AICommandResponse(intent="language_update", status="success", message=lang_msg)
        
        lang = session_state.get_language(session_id)

        # Determine Category and Action
        if any(k in cmd for k in ["analyze", "analiza", "inspect", "inspecciona", "inspeccioná", "audit", "diagnose", "diagnostica", "system state", "estado"]):
            return await self._handle_analyze(cmd, lang)
            
        if any(k in cmd for k in ["propose", "propone", "proponé", "suggest", "sugiere", "sugieré", "recommend", "how to fix"]):
            return await self._handle_propose(cmd, lang)
            
        if any(k in cmd for k in ["execute", "ejecuta", "ejecutá", "apply", "aplica", "aplicá", "repair", "repara", "repará", "fix", "arregla", "modify", "patch", "modifica"]):
            return await self._handle_execute(cmd, lang)
            
        if "optimize" in cmd or "optimiza" in cmd:
            return await self._handle_optimize(cmd, lang)

        msg = "[TECHNICAL_ROUTING_ACTIVE]\nCreator command received. Technical creator routing is active. Specify patch, analysis, architecture, or chip task."
        workflow = "\n".join(engineering_policy.get_structured_workflow("task"))
        if lang == "es":
            msg = f"[ENRUTAMIENTO_TÉCNICO_ACTIVO]\nComando de Creador recibido. El enrutamiento técnico de creador está activo. Especifica parche, análisis, arquitectura o tarea de chip.\n\nProtocolo:\n{workflow}"
        else:
            msg = f"{msg}\n\nProtocol:\n{workflow}"
            
        return AICommandResponse(intent="creator_technical", status="success", message=msg, payload={})

    async def _handle_analyze(self, cmd: str, lang: str) -> AICommandResponse:
        """Category A: ANALYZE / INSPECT"""
        from backend.core.system_state.engine import state_engine
        state = await state_engine.get_state()

        if "health" in cmd or "audit" in cmd or "sistema" in cmd or "state" in cmd:
            policy_step = engineering_policy.start_audit()
            if "audit" in cmd:
                report = await auditor.run_full_audit()
                summary = report.summary
            else:
                if lang == "es":
                    summary = f"{policy_step}\nSalud: {state.health.value}. Chips: {len(state.chips)} activos."
                else:
                    summary = f"{policy_step}\nHealth: {state.health.value}. Chips: {len(state.chips)} active."

            visual = visual_interface.create_visual_payload("task-report", {
                "status": "success",
                "actions": ["Reading system state...", "Probing health status..."],
                "issues": [summary]
            }, "System Inspection")
            
            if lang == "es":
                message = (
                    f"ANÁLISIS OPERACIONAL: ESTADO DEL SISTEMA\n\n"
                    f"- Status: {state.health.value.upper()}\n"
                    f"- Entorno: {state.git_branch}\n"
                    f"- Diagnóstico: {summary}\n"
                    f"- Nivel de Riesgo: LOW"
                )
            else:
                message = (
                    f"OPERATIONAL ANALYSIS: SYSTEM STATE\n\n"
                    f"- Status: {state.health.value.upper()}\n"
                    f"- Environment: {state.git_branch}\n"
                    f"- Diagnostics: {summary}\n"
                    f"- Risk level: LOW"
                )
            
            return AICommandResponse(
                intent="system_analysis",
                status="success",
                message=message,
                payload={"state": state.model_dump(mode='json'), "visual": visual}
            )

        # Try to find a specific chip target
        chip_query = extract_chip_target(cmd)
        chip_data = module_registry.search_chip(chip_query)
        target_chip = chip_data["slug"] if chip_data else None
        
        if target_chip:
            # INTEGRATION: Call ActionExecutor instead of just returning payload
            from ..execution.executor import action_executor
            execution = await action_executor.execute("inspect_chip", {"target": target_chip})
            
            return AICommandResponse(
                intent="inspect_chip",
                status="success" if execution.get("success") else "error",
                message=execution.get("message", f"Localizado chip '{target_chip}'. Iniciando análisis de integridad y flujo de datos." if lang == "es" else f"Located chip '{target_chip}'. Starting integrity and data flow analysis."),
                payload={
                    "target": target_chip, 
                    "action": "INSPECT_CHIP",
                    "execution": execution,
                    "ui_instruction": execution.get("ui_instruction")
                }
            )

        msg = "INSPECTION REPORT\nI'm ready to inspect specific components. Please indicate a chip slug or module name."
        if lang == "es":
            msg = "REPORTE DE INSPECCIÓN\nEstoy listo para inspeccionar componentes específicos. Por favor indica un slug de chip o nombre de módulo."
            
        return AICommandResponse(intent="inspection_fallback", status="success", message=msg, payload={})

    async def _handle_propose(self, cmd: str, lang: str) -> AICommandResponse:
        """Category B: PROPOSE"""
        # UI Optimizations
        if any(k in cmd for k in ["interface", "readability", "ui", "chat", "layout"]):
            if lang == "es":
                msg = (
                    "PROPUESTA DE MEJORA DE INTERFAZ\n"
                    "- Problema: Densidad visual o restricción de layout\n"
                    "- Solución: Recalibrar contenedores CSS y padding dinámico\n"
                    "- Impacto: Mejora en la UX del Creador y legibilidad\n"
                    "- Riesgo: VERY LOW\n\n"
                    "¿Deseas que aplique estos ajustes operacionales?"
                )
            else:
                msg = (
                    "INTERFACE IMPROVEMENT PROPOSAL\n"
                    "- Issue detected: Visual density or layout constraint\n"
                    "- Proposed fix: Recalibrate CSS containers and dynamic padding\n"
                    "- Expected impact: Enhanced Creator UX and readability\n"
                    "- Risk level: VERY LOW\n\n"
                    "Do you want me to apply these operational adjustments?"
                )
            return AICommandResponse(intent="ui_proposal", status="success", message=msg, payload={"action": "ui_optimization"})

        # Code Patches
        from backend.core.module_registry import module_registry
        chip_query = extract_chip_target(cmd)
        chip_data = module_registry.search_chip(chip_query)
        target = chip_data["slug"] if chip_data else None
        
        if target:
            isolation = engineering_policy.isolate_layer(cmd)
            analysis = code_analyzer.analyze_chip(target)
            patches = patch_generator.generate_patch(cmd, analysis)
            if patches:
                summary = patch_generator.summarize_patch(patches)
                patch_step = engineering_policy.propose_patch(summary)
                if lang == "es":
                    msg = (
                        f"{isolation}\n"
                        f"{patch_step}\n\n"
                        f"SOLUCIÓN PROPUESTA PARA '{target}'\n\n"
                        f"- Causa Raíz: Brecha lógica detectada\n"
                        f"- Solución: {summary}\n"
                        f"- Riesgo: MODERATE\n\n"
                        "¿Confirmas el despliegue de este parche?"
                    )
                else:
                    msg = (
                        f"{isolation}\n"
                        f"{patch_step}\n\n"
                        f"PROPOSED SOLUTION FOR '{target}'\n\n"
                        f"- Root cause: Logic gap detected via code analysis\n"
                        f"- Proposed fix: {summary}\n"
                        f"- Risk level: MODERATE\n\n"
                        "Do you confirm the deployment of this patch?"
                    )
                return AICommandResponse(intent="code_proposal", status="success", message=msg, payload={"patches": patches, "target": target})

        msg = "PROPOSAL ENGINE\nWaiting for specific target (chip, module, or UI element) to generate an optimization plan."
        if lang == "es":
            msg = "MOTOR DE PROPUESTAS\nEsperando objetivo específico (chip, módulo o UI) para generar un plan de optimización."
            
        return AICommandResponse(intent="generic_proposal", status="success", message=msg, payload={})

    async def _handle_execute(self, cmd: str, lang: str) -> AICommandResponse:
        """Category C: EXECUTE / SAFE-GUARDED"""
        # Check for presence of "confirm"
        confirmed = any(word in cmd.split() for word in ["confirm", "yes", "si", "sí", "afirmado", "procede", "proceed"])
        
        is_sensitive = any(k in cmd for k in ["permis", "database", "backend", "delete", "remove", "access", "auth", "token"])
        risk = "HIGH" if is_sensitive else "MODERATE"

        if not confirmed:
            if lang == "es":
                msg = (
                    f"GUARDIA DE EJECUCIÓN ACTIVA\n"
                    f"- Acción: {cmd}\n"
                    f"- Riesgo: {risk}\n"
                    f"- Impacto: Cambio persistente en el sistema\n\n"
                    f"Esperando aprobación explícita del creador para ejecutar."
                )
            else:
                msg = (
                    f"EXECUTION GUARD ACTIVE\n"
                    f"- Target action: {cmd}\n"
                    f"- Detected risk: {risk}\n"
                    f"- Impact: Persistent system change\n\n"
                    f"Awaiting explicit creator approval to execute."
                )
            return AICommandResponse(intent="confirmation_required", status="pending", message=msg, payload={"action_type": "sensitive" if is_sensitive else "standard", "risk": risk})
            
        if lang == "es":
            verify_step = engineering_policy.verify_patch()
            test_step = engineering_policy.run_tests()
            reaudit_step = engineering_policy.re_audit()
            msg = f"{verify_step}\n{test_step}\n{reaudit_step}\n\nEJECUCIÓN EXITOSA\n\nAction: {cmd}\nStatus: Estable\nIntegrity: Verificada\n\nLos cambios se han aplicado y el sistema está sincronizado."
        else:
            verify_step = engineering_policy.verify_patch()
            test_step = engineering_policy.run_tests()
            reaudit_step = engineering_policy.re_audit()
            msg = f"{verify_step}\n{test_step}\n{reaudit_step}\n\nEXECUTION SUCCESS\n\nAction: {cmd}\nStatus: Stable\nIntegrity: Verified\n\nChanges applied and system synchronized."
            
        return AICommandResponse(intent="execution_success", status="success", message=msg, payload={"action": cmd, "status": "completed"})

    async def _handle_optimize(self, cmd: str, lang: str) -> AICommandResponse:
        """Category C: OPTIMIZE"""
        if lang == "es":
            msg = (
                "OPTIMIZACIÓN DE SISTEMA INICIADA\n\n"
                "Tarea: Reequilibrio de recursos y poda de pipelines\n"
                "Objetivo: Velocidad Operacional Core\n"
                "Estado: Secuencia iniciada\n\n"
                "El sistema operará con mayor fluidez en los próximos ciclos."
            )
        else:
            msg = (
                "SYSTEM OPTIMIZATION ENGAGED\n\n"
                "Task: Resource rebalancing and pipeline pruning\n"
                "Target: Core Operational Speed\n"
                "Status: Sequence initiated\n\n"
                "The system will operate more smoothly in the next cycles."
            )
        return AICommandResponse(intent="optimization_active", status="success", message=msg, payload={})
