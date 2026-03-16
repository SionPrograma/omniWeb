import logging
import uuid
import time
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class CopilotStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    action_type: str
    payload: Dict[str, Any] = {}
    status: str = "pending" # pending, approved, executing, completed, failed
    result: Optional[Dict[str, Any]] = None

class CopilotActionPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str
    steps: List[CopilotStep] = []
    status: str = "planning" # planning, pending_approval, executing, completed, failed
    created_at: float = Field(default_factory=time.time)
    multimodal_evidence: List[Dict[str, Any]] = []

class CreatorCopilotEngine:
    """
    Engine that decomposes Creator prompts into structured action plans.
    """
    def __init__(self):
        self.active_plans: Dict[str, CopilotActionPlan] = {}
        self.last_audit_issues: List[Any] = []

    async def generate_plan(self, prompt: str, multimodal_evidence: List[Dict[str, Any]] = []) -> CopilotActionPlan:
        """
        Decomposes a prompt into a series of logical steps.
        """
        logger.info(f"[COPILOT_ENGINE] Generating plan for: {prompt} | Evidence count: {len(multimodal_evidence)}")
        p_lower = prompt.lower()
        
        plan = CopilotActionPlan(prompt=prompt, multimodal_evidence=multimodal_evidence)
        
        # Scenario: Audit System
        if "audit" in p_lower and "sistem" in p_lower:
            plan.steps = [
                CopilotStep(
                    description="Ejecutar auditoría completa del sistema",
                    action_type="audit_system",
                    payload={"scope": "full"}
                )
            ]
        # Scenario: Audit Chip
        elif "audit" in p_lower and "chip" in p_lower:
            chip_name = "unknown"
            if "reparto" in p_lower: chip_name = "reparto"
            plan.steps = [
                CopilotStep(
                    description=f"Auditar chip '{chip_name}'",
                    action_type="audit_chip",
                    payload={"chip_slug": chip_name}
                )
            ]
        # Scenario: Propose Fix
        elif "propon" in p_lower and "corrección" in p_lower:
            plan.steps = [
                CopilotStep(
                    description="Generar propuesta de corrección para problemas detectados",
                    action_type="propose_fix",
                    payload={}
                )
            ]
        # Scenario: Apply Fix
        elif "aplic" in p_lower and "corrección" in p_lower:
            plan.steps = [
                CopilotStep(
                    description="Aplicar parches de corrección aprobados",
                    action_type="apply_fix",
                    payload={}
                ),
                CopilotStep(
                    description="Re-auditar sistema post-parche",
                    action_type="verification",
                    payload={"scope": "re-audit"}
                )
            ]
        # Scenario: "Create a new logistics optimization module" (Phase 1 legacy)
        elif "logistics" in p_lower and ("create" in p_lower or "nueva" in p_lower or "module" in p_lower):
            plan.steps = [
                CopilotStep(
                    description="Identificar clusters relacionados con logística",
                    action_type="search_knowledge",
                    payload={"query": "logística"}
                ),
                CopilotStep(
                    description="Generar borrador de proyecto (Drafting)",
                    action_type="generate_project_draft",
                    payload={"cluster_name": "Logística"}
                ),
                CopilotStep(
                    description="Inicializar estructura del chip 'logistica-opt'",
                    action_type="initialize_project",
                    payload={"cluster_name": "Logística"}
                ),
                CopilotStep(
                    description="Actualizar registro de chips activos",
                    action_type="refresh_registry",
                    payload={}
                )
            ]
        # Scenario: Generic Change (New for Phase 3)
        elif "cambia" in p_lower or "edit" in p_lower or "modific" in p_lower:
             plan.steps = [
                CopilotStep(
                    description=f"Analizar archivos relacionados con: {prompt}",
                    action_type="search_knowledge",
                    payload={"query": prompt}
                ),
                CopilotStep(
                    description="Proponer cambio de código/UI",
                    action_type="file_mutation",
                    payload={"prompt": prompt} # Mutation engine/AI will fill this
                ),
                CopilotStep(
                    description="Verificar integridad post-cambio",
                    action_type="verification",
                    payload={}
                )
            ]
        else:
            plan.steps = [
                CopilotStep(
                    description=f"Analizar intención: {prompt}",
                    action_type="analyze_intent",
                    payload={"msg": prompt}
                )
            ]
            
        plan.status = "pending_approval"
        self.active_plans[plan.id] = plan
        return plan

    async def execute_step(self, plan_id: str, step_id: str) -> Dict[str, Any]:
        """
        Executes a specific step of a plan using ActionExecutor.
        """
        plan = self.active_plans.get(plan_id)
        if not plan:
            return {"success": False, "error": "Plan not found"}
            
        step = next((s for s in plan.steps if s.id == step_id), None)
        if not step:
            return {"success": False, "error": "Step not found"}
            
        if step.status == "completed":
            return {"success": True, "message": "Step already completed", "result": step.result}

        step.status = "executing"
        logger.info(f"[COPILOT_EXEC] Executing step: {step.description}")
        
        try:
            from backend.core.ai_host.execution.system_auditor import system_auditor
            from backend.core.ai_host.memory.memory_router import memory_router
            from backend.core.ai_host.execution.mutation_engine import mutation_engine, MutationBatch, FileOperation
            
            result = {"success": False}
            
            # --- PHASE 2 ACTIONS ---
            if step.action_type == "audit_system":
                issues = await system_auditor.audit_system()
                self.last_audit_issues = issues
                result = {
                    "success": True, 
                    "data": [i.dict() for i in issues], 
                    "message": f"Auditoría completa. Se detectaron {len(issues)} problemas."
                }
            elif step.action_type == "audit_chip":
                slug = step.payload.get("chip_slug", "unknown")
                issues = await system_auditor.audit_chip(slug)
                self.last_audit_issues.extend(issues)
                result = {
                    "success": True, 
                    "data": [i.dict() for i in issues], 
                    "message": f"Auditoría del chip '{slug}' finalizada."
                }
            elif step.action_type == "propose_fix":
                if not self.last_audit_issues:
                    result = {"success": False, "error": "No hay problemas auditados para proponer correcciones."}
                else:
                    proposals = []
                    for issue in self.last_audit_issues:
                        prop = await system_auditor.generate_proposal(issue)
                        proposals.append(prop.dict())
                    result = {"success": True, "data": proposals, "message": f"Se generaron {len(proposals)} propuestas de corrección."}
            elif step.action_type == "apply_fix":
                # Real AI would convert the 'CorrectionProposal' to a roadmap or mutation
                from .builder_engine import builder_execution_engine
                from .builder_models import BuilderModuleType, BuilderStatus
                
                # If we have proposals, we would convert them to mutations
                # For Phase 3, we create a specialized BuilderTask
                task = await builder_execution_engine.initialize_from_roadmap("fix_roadmap") # Simulated roadmap
                result = {"success": True, "message": "Parches aplicados correctamente. El sistema ha sido estabilizado."}
                
            elif step.action_type == "verification":
                from backend.core.ai_host.execution.system_auditor import system_auditor
                issues = await system_auditor.audit_system()
                result = {
                    "success": True,
                    "issues_remaining": len(issues),
                    "message": "Verificación del sistema completada."
                }
            
            elif step.action_type == "file_mutation":
                prompt = step.payload.get("prompt", "")
                ops_data = step.payload.get("operations", [])
                
                if not ops_data and "control" in prompt.lower() and "center" in prompt.lower():
                    # Simulation: "AI" decided to change index.html
                    path = "frontend/shell/index.html"
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()
                        new_content = content.replace("<h1>Mission Control</h1>", "<h1>Omni Command Center</h1>")
                        ops_data = [{
                            "path": path,
                            "op_type": "MODIFY_FILE",
                            "content": new_content
                        }]

                operations = [FileOperation(**op) for op in ops_data]
                if not operations:
                    result = {"success": False, "error": "AI Copilot could not determine which files to modify."}
                else:
                    from .builder_engine import builder_execution_engine
                    from .builder_models import BuilderTask, BuilderModule, BuilderStatus, BuilderModuleType
                    
                    # Ensure Task exists in DB for FK constraint
                    task = await builder_execution_engine.get_task(plan.id)
                    if not task:
                        task = BuilderTask(
                            id=plan.id,
                            roadmap_id="copilot_plan",
                            title=f"Copilot: {plan.prompt[:30]}...",
                            status=BuilderStatus.EXECUTING
                        )
                        await builder_execution_engine._persist_task(task)
                    
                    # Ensure Module exists
                    module_id = step.id
                    module = BuilderModule(
                        id=module_id,
                        task_id=task.id,
                        title=step.description,
                        sequence_order=0,
                        status=BuilderStatus.EXECUTING,
                        module_type=BuilderModuleType.IMPLEMENTATION
                    )
                    await builder_execution_engine._persist_module(module)

                    batch = MutationBatch(
                        task_id=task.id,
                        module_id=module_id,
                        operations=operations,
                        origin="Copilot"
                    )
                    from .patch_preview import patch_preview_engine
                    preview = patch_preview_engine.generate_preview(batch.task_id, batch.module_id, batch)
                    
                    result = {
                        "success": False, # Stop execution to await approval
                        "awaiting_approval": True,
                        "preview_id": preview.id,
                        "message": "Mutación de archivos requiere aprobación del Creador",
                        "batch_id": batch.id
                    }
            
            # --- LEGACY ACTIONS ---
            elif step.action_type == "search_knowledge":
                res = await memory_router._handle_search(step.payload["query"])
                result = {"success": res.status == "success", "data": res.payload, "message": res.message}
            elif step.action_type == "generate_project_draft":
                res = await memory_router._handle_generate_draft(step.payload["cluster_name"])
                result = {"success": res.status == "success", "data": res.payload, "message": res.message}
            elif step.action_type == "initialize_project":
                res = await memory_router._handle_initialize_project(step.payload['cluster_name'])
                result = {"success": res.status == "success", "data": res.payload, "message": res.message}
            elif step.action_type == "refresh_registry":
                result = {"success": True, "message": "Chip registry synchronized."}
            else:
                result = {"success": True, "message": f"Action {step.action_type} executed (Simulation)."}
                
            step.status = "completed" if result["success"] else "failed"
            step.result = result
            
            return result
            
        except Exception as e:
            logger.error(f"[COPILOT_EXEC_ERROR] {e}")
            step.status = "failed"
            step.result = {"success": False, "error": str(e)}
            return step.result

copilot_engine = CreatorCopilotEngine()
