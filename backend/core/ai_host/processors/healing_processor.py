import logging
from typing import Dict, Any, List
from .base import CommandProcessor, AICommandResponse
from backend.core.system_auditor.auditor import auditor
from backend.core.system_auditor.fix_engine import fix_engine
from backend.core.system_auditor.models import AuditStatus

logger = logging.getLogger(__name__)

class HealingProcessor(CommandProcessor):
    """
    AI Host Processor for Self-Healing and System Auditing.
    Phase 8: Auto Fix Engine.
    """
    
    async def can_handle(self, message: str) -> bool:
        keywords = ["audit", "salud", "problema", "fix", "healing", "arregla", "cura", "sana"]
        return any(k in message.lower() for k in keywords)

    async def process(self, message: str, context: str = "default_user") -> AICommandResponse:
        msg = message.lower()
        
        # 1. Trigger Audit
        if any(k in msg for k in ["audita", "revisa", "check health", "run audit"]):
            report = await auditor.run_full_audit()
            status_icon = "✅" if report.overall_status == AuditStatus.PASS else "⚠️"
            
            res_msg = f"### {status_icon} Informe de Salud del Sistema\n"
            res_msg += f"- **Estado**: {report.overall_status.value}\n"
            res_msg += f"- **Resumen**: {report.summary}\n\n"
            
            fixes = list(fix_engine.active_proposals.values())
            if fixes:
                res_msg += "#### 🔧 Acciones de Autocuración Disponibles:\n"
                for f in fixes:
                    res_msg += f"- **{f.id}**: {f.analysis}\n"
                res_msg += "\n¿Deseas que aplique alguna de estas soluciones?"
            
            return AICommandResponse(
                intent="system_audit",
                status="success",
                message=res_msg,
                payload={"report": report.model_dump(mode='json'), "fixes_available": len(fixes)}
            )

        # 2. List Fixes
        if any(k in msg for k in ["qué problemas", "listar fixes", "soluciones", "fixes"]):
            fixes = list(fix_engine.active_proposals.values())
            if not fixes:
                return AICommandResponse(
                    intent="list_fixes",
                    status="success",
                    message="No he detectado problemas que requieran autocuración en este momento. ¡El sistema está estable!"
                )
            
            res_msg = "### 🔧 Soluciones de Autocuración\n"
            for f in fixes:
                res_msg += f"- **{f.id}**: {f.analysis} ({len(f.actions)} acciones)\n"
            
            return AICommandResponse(
                intent="list_fixes",
                status="success",
                message=res_msg,
                payload={"fixes": [f.model_dump(mode='json') for f in fixes]}
            )

        # 3. Apply Fix
        if "aplica" in msg or "fix" in msg or "arregla" in msg:
            # Try to find a proposal ID in the message
            target_id = None
            for p_id in fix_engine.active_proposals.keys():
                if p_id in msg:
                    target_id = p_id
                    break
            
            if not target_id:
                # If no ID but they say "arregla todo" or similar
                fixes = list(fix_engine.active_proposals.values())
                if fixes:
                    target_id = fixes[0].id # Take the first one for now
                else:
                    return AICommandResponse(
                        intent="apply_fix",
                        status="error",
                        message="No pude identificar qué fix aplicar o no hay problemas detectados."
                    )
            
            proposal = fix_engine.active_proposals.get(target_id)
            
            # Request Confirmation (Integrates with Shell Permission)
            if "confirm" not in msg:
                return AICommandResponse(
                    intent="confirmation_required",
                    status="pending",
                    message=f"⚠️ **Confirmación de Autocuración**: Estoy a punto de aplicar el fix `{target_id}`:\n\n_{proposal.analysis}_\n\n¿Procedo con la reparación?",
                    payload={"action": "apply_fix", "proposal_id": target_id}
                )

            # Execution
            success = await fix_engine.apply_fix(target_id)
            if success:
                # Re-audit
                report = await auditor.run_full_audit()
                del fix_engine.active_proposals[target_id] # Clear after success
                
                return AICommandResponse(
                    intent="apply_fix_success",
                    status="success",
                    message=f"✅ **Autocuración Completada**: El fix `{target_id}` se ha aplicado con éxito. Nuevo estado del sistema: **{report.overall_status.value}**.",
                    payload={"new_report": report.model_dump(mode='json')}
                )
            else:
                 return AICommandResponse(
                    intent="apply_fix_error",
                    status="error",
                    message=f"❌ Falló el intento de autocuración para `{target_id}`. He registrado el error en el Logbook Maestro."
                )

        return AICommandResponse(
            intent="healing_unknown",
            status="success",
            message="Puedo auditar el sistema o aplicar soluciones de autocuración. ¿Qué necesitas?"
        )
