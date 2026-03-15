import logging
import asyncio
import json
import time
from typing import List, Dict, Optional, Any
from .builder_models import BuilderTask, BuilderModule, BuilderStatus, BuilderModuleType
from ..memory.project_manager import project_manager
from .copilot_engine import copilot_engine
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class BuilderExecutionEngine:
    """
    Executes approved roadmaps step-by-step.
    Coordinates between ProjectManager (for scaffolding) and Copilot (for logic/actions).
    """
    def __init__(self):
        self.active_tasks: Dict[str, BuilderTask] = {}
        self._execution_lock = asyncio.Lock()

    async def initialize_from_roadmap(self, roadmap_entry: Any) -> BuilderTask:
        """
        Converts a MasterLogbookEntry (roadmap type) into a BuilderTask.
        """
        logger.info(f"[BUILDER_ENGINE] Initializing task from roadmap: {roadmap_entry.id}")
        
        try:
            # Assuming roadmap_entry.content is JSON or has a structure
            # If it's plain text, we might need a parser, but usually roadmaps are structured.
            data = {}
            if roadmap_entry.content.strip().startswith('{'):
                data = json.loads(roadmap_entry.content)
            else:
                # Fallback: Treat as title
                data = {"title": roadmap_entry.content, "modules": []}

            task = BuilderTask(
                roadmap_id=roadmap_entry.id,
                title=data.get("title", "Unnamed Roadmap"),
                metadata=roadmap_entry.metadata
            )

            # Create modules from roadmap data
            modules_data = data.get("modules", [])
            for i, mod_data in enumerate(modules_data):
                module = BuilderModule(
                    task_id=task.id,
                    title=mod_data.get("title", f"Module {i+1}"),
                    description=mod_data.get("description"),
                    sequence_order=i,
                    module_type=mod_data.get("type", BuilderModuleType.IMPLEMENTATION),
                    payload=mod_data.get("payload", {})
                )
                task.modules.append(module)

            self.active_tasks[task.id] = task
            await self._persist_task(task)
            
            for mod in task.modules:
                await self._persist_module(mod)

            return task
        except Exception as e:
            logger.error(f"[BUILDER_ENGINE_INIT_ERROR] {e}")
            raise

    async def get_task(self, task_id: str) -> Optional[BuilderTask]:
        """Retrieves a task from memory or DB."""
        return self.active_tasks.get(task_id) or await self._load_task(task_id)

    async def start_execution(self, task_id: str):
        """
        Starts sequential execution of modules in a task.
        """
        task = self.active_tasks.get(task_id) or await self._load_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.status == BuilderStatus.EXECUTING:
            logger.warning(f"Task {task_id} is already executing")
            return

        task.status = BuilderStatus.EXECUTING
        await self._persist_task(task)

        # Run in background
        asyncio.create_task(self._execute_loop(task))

    async def retry_module(self, task_id: str, module_id: str):
        """Resets a failed module and restarts execution."""
        task = self.active_tasks.get(task_id)
        if not task: return
        
        module = next((m for m in task.modules if m.id == module_id), None)
        if module:
            module.status = BuilderStatus.PENDING
            module.error = None
            module.progress = 0
            task.status = BuilderStatus.EXECUTING
            await self._persist_module(module)
            await self._persist_task(task)
            asyncio.create_task(self._execute_loop(task))

    async def skip_module(self, task_id: str, module_id: str):
        """Marks a module as completed (manual override) and continues."""
        task = self.active_tasks.get(task_id)
        if not task: return
        
        module = next((m for m in task.modules if m.id == module_id), None)
        if module:
            module.status = BuilderStatus.COMPLETED
            module.progress = 100.0
            await self._persist_module(module)
            if task.status != BuilderStatus.EXECUTING:
                task.status = BuilderStatus.EXECUTING
                await self._persist_task(task)
                asyncio.create_task(self._execute_loop(task))

    async def _execute_loop(self, task: BuilderTask):
        async with self._execution_lock:
            logger.info(f"[BUILDER_EXEC] Starting execution loop for task: {task.title}")
            
            # Sort modules by sequence order
            modules = sorted(task.modules, key=lambda m: m.sequence_order)
            
            for module in modules:
                if module.status == BuilderStatus.COMPLETED:
                    continue
                
                if task.status in [BuilderStatus.CANCELLED, BuilderStatus.FAILED]:
                    break

                task.current_module_id = module.id
                await self._persist_task(task)

                success = await self._execute_module(task, module)
                
                if not success:
                    if module.status == BuilderStatus.AWAITING_APPROVAL:
                        logger.info(f"[BUILDER_EXEC] Module {module.title} awaiting approval. Pausing task.")
                        task.status = BuilderStatus.AWAITING_APPROVAL
                        await self._persist_task(task)
                        return # Pause execution
                    
                    task.status = BuilderStatus.FAILED
                    await self._persist_task(task)
                    logger.error(f"[BUILDER_EXEC] Module {module.title} failed. Stopping task.")
                    break
                
                # Update task progress
                completed_count = len([m for m in task.modules if m.status == BuilderStatus.COMPLETED])
                task.progress = (completed_count / len(task.modules)) * 100
                task.last_update = time.time()
                await self._persist_task(task)

            if task.status == BuilderStatus.EXECUTING:
                task.status = BuilderStatus.COMPLETED
                task.progress = 100.0
                await self._persist_task(task)
                logger.info(f"[BUILDER_EXEC] Task {task.title} completed successfully.")
                
                # Trigger Audit Verification (Phase 3 Requirement)
                await self._trigger_post_execution_audit(task)

    async def _execute_module(self, task: BuilderTask, module: BuilderModule) -> bool:
        logger.info(f"[BUILDER_MOD] Executing module: {module.title} ({module.module_type})")
        module.status = BuilderStatus.EXECUTING
        module.progress = 10.0
        await self._persist_module(module)

        try:
            # COORDINATION WITH COPILOT / PROJECT MANAGER
            if module.module_type == BuilderModuleType.INITIALIZATION:
                # Use ProjectManager to initialize
                # Payload should contain draft description
                from ..synthesis.synthesis_engine import ProjectDraft
                draft = ProjectDraft(
                    title=module.payload.get("project_title", task.title),
                    summary=module.description or "",
                    suggested_modules=module.payload.get("modules", []),
                    suggested_next_steps=module.payload.get("steps", [])
                )
                res = project_manager.initialize_project(draft)
                module.result = res
                if res.get("status") == "success":
                    module.progress = 100.0
                    module.status = BuilderStatus.COMPLETED
                else:
                    module.status = BuilderStatus.FAILED
                    module.error = res.get("message")
            
            elif module.module_type == BuilderModuleType.IMPLEMENTATION:
                # 1. Check for direct mutations in payload (Priority for fast execution)
                if module.payload.get("mutations"):
                    from .mutation_engine import mutation_engine, MutationBatch, FileOperation
                    ops = [FileOperation(**op) for op in module.payload["mutations"]]
                    batch = MutationBatch(
                        task_id=task.id,
                        module_id=module.id,
                        operations=ops,
                        origin="Builder"
                    )
                    from .patch_preview import patch_preview_engine
                    preview = patch_preview_engine.generate_preview(task.id, module.id, batch)
                    module.status = BuilderStatus.AWAITING_APPROVAL
                    module.result = {"preview_id": preview.id, "type": "patch_preview"}
                    await self._persist_module(module)
                    return False # Return False but status is AWAITING_APPROVAL

                # 2. Use Copilot if no direct mutations
                prompt = f"Implement module '{module.title}': {module.description}"
                if module.payload.get("context"):
                    prompt += f" Context: {module.payload['context']}"
                
                plan = await copilot_engine.generate_plan(prompt)
                module.progress = 20.0
                await self._persist_module(module)

                # Execute all steps of the plan
                for i, step in enumerate(plan.steps):
                    task.current_submodule = step.description
                    module.current_submodule = step.description
                    await self._persist_task(task)
                    await self._persist_module(module)

                    step_res = await copilot_engine.execute_step(plan.id, step.id)
                    if step_res.get("awaiting_approval"):
                        module.status = BuilderStatus.AWAITING_APPROVAL
                        module.result = {"preview_id": step_res.get("preview_id"), "type": "patch_preview"}
                        await self._persist_module(module)
                        return False # Pause loop

                    if not step_res.get("success"):
                        module.status = BuilderStatus.FAILED
                        module.error = f"Step {i+1} failed: {step_res.get('error')}"
                        break
                    
                    # Dynamic progress update
                    module.progress = 20.0 + ((i + 1) / len(plan.steps)) * 70.0
                    module.last_update = time.time()
                    await self._persist_module(module)
                
                if module.status != BuilderStatus.FAILED:
                    module.status = BuilderStatus.COMPLETED
                    module.progress = 100.0
            
            elif module.module_type == BuilderModuleType.AUDIT:
                # Use Copilot's audit system - creating a temporary plan/step context
                module.progress = 50.0
                await self._persist_module(module)

                from backend.core.ai_host.execution.system_auditor import system_auditor
                issues = await system_auditor.audit_system()
                module.result = {"success": True, "issues_found": len(issues), "message": "Audit completed."}
                module.status = BuilderStatus.COMPLETED
                module.progress = 100.0

            else:
                # Unknown type - simulation
                await asyncio.sleep(2)
                module.status = BuilderStatus.COMPLETED
                module.progress = 100.0

            await self._persist_module(module)
            return module.status == BuilderStatus.COMPLETED

        except Exception as e:
            logger.error(f"[BUILDER_MOD_ERROR] {e}")
            module.status = BuilderStatus.FAILED
            module.error = str(e)
            await self._persist_module(module)
            return False

    async def _persist_task(self, task: BuilderTask):
        try:
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO builder_tasks (id, roadmap_id, title, status, progress, current_module_id, current_submodule, last_update, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.id, task.roadmap_id, task.title, task.status.value,
                    task.progress, task.current_module_id, task.current_submodule,
                    task.last_update, json.dumps(task.metadata)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[BUILDER_PERSIST_TASK_ERROR] {e}")

    async def _persist_module(self, module: BuilderModule):
        try:
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO builder_modules (id, task_id, title, description, status, progress, sequence_order, module_type, payload, result, error, current_submodule, last_update)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    module.id, module.task_id, module.title, module.description,
                    module.status.value, module.progress, module.sequence_order,
                    module.module_type.value, json.dumps(module.payload),
                    json.dumps(module.result) if module.result else None,
                    module.error, module.current_submodule, module.last_update
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[BUILDER_PERSIST_MOD_ERROR] {e}")

    async def _load_task(self, task_id: str) -> Optional[BuilderTask]:
        """Loads a task and its modules from the database."""
        try:
            with db_manager.get_connection() as conn:
                task_row = conn.execute("SELECT * FROM builder_tasks WHERE id = ?", (task_id,)).fetchone()
                if not task_row:
                    return None
                
                task = BuilderTask(
                    id=task_row["id"],
                    roadmap_id=task_row["roadmap_id"],
                    title=task_row["title"],
                    status=BuilderStatus(task_row["status"]),
                    progress=task_row["progress"],
                    current_module_id=task_row["current_module_id"],
                    current_submodule=task_row["current_submodule"],
                    last_update=task_row["last_update"] or time.time(),
                    metadata=json.loads(task_row["metadata"]) if task_row["metadata"] else {}
                )
                
                mod_rows = conn.execute("SELECT * FROM builder_modules WHERE task_id = ? ORDER BY sequence_order", (task_id,)).fetchall()
                for m in mod_rows:
                    mod = BuilderModule(
                        id=m["id"],
                        task_id=m["task_id"],
                        title=m["title"],
                        description=m["description"],
                        status=BuilderStatus(m["status"]),
                        progress=m["progress"],
                        sequence_order=m["sequence_order"],
                        module_type=BuilderModuleType(m["module_type"]),
                        payload=json.loads(m["payload"]) if m["payload"] else {},
                        result=json.loads(m["result"]) if m["result"] else None,
                        error=m["error"],
                        current_submodule=m["current_submodule"],
                        last_update=m["last_update"] or time.time()
                    )
                    task.modules.append(mod)
                
                self.active_tasks[task.id] = task
                return task
        except Exception as e:
            logger.error(f"[BUILDER_LOAD_TASK_ERROR] {e}")
            return None

    async def _trigger_post_execution_audit(self, task: BuilderTask):
        logger.info(f"[BUILDER_AUDIT] Triggering post-execution audit for: {task.title}")
        # In a real scenario, this would call the Auditor directly or create a new audit task.
        pass

builder_execution_engine = BuilderExecutionEngine()
