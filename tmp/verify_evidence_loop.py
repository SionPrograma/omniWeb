import asyncio
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.core.ai_host.orchestration.execution_tree import tree_planner, ExecutionNode, NodeStatus
from backend.core.ai_host.orchestration.evidence_loop import evidence_loop
from backend.core.ai_host.orchestration.prompt_compiler import CompiledMission

async def test_evidence_loop():
    print("\n--- [1] Mocking Mission Tree ---")
    mission = CompiledMission(
        mission_name="Test Verificación",
        primary_objective="Validar el Evidence Loop",
        critical_files=["backend/core/ai_host/orchestration/evidence_loop.py"]
    )
    tree = tree_planner.generate(mission)
    root = tree.root
    
    # Let's find one phase 2 task
    task_node = None
    for phase in root.children:
        if "Fase 2" in phase.label:
            task_node = phase.children[0] # The "Modificar..." task
            break
            
    if not task_node:
        print("FAIL: Task node not found in generated tree.")
        return

    print(f"Target Node: {task_node.label} (Type: {task_node.verification_type})")

    print("\n--- [2] Testing PASSED Verification (File exists) ---")
    # Change type to file_check for easier test
    task_node.verification_type = "file_check"
    task_node.metadata["target_file"] = os.path.abspath("backend/core/ai_host/orchestration/evidence_loop.py")
    
    evidence = evidence_loop.verify_node(task_node)
    print(f"Passed: {evidence.passed}")
    print(f"Details: {evidence.details}")
    
    evidence_loop.close_node(task_node, evidence)
    print(f"Node Status: {task_node.status}")
    
    if task_node.status == NodeStatus.COMPLETED:
        print("PASS: Node marked as DONE.")
    else:
        print("FAIL: Node status not updated correctly.")

    print("\n--- [3] Testing FAILED Verification (File missing) ---")
    task_node.status = NodeStatus.PENDING # reset
    task_node.metadata["target_file"] = "non_existent_file.py"
    
    evidence_fail = evidence_loop.verify_node(task_node)
    print(f"Passed: {evidence_fail.passed}")
    print(f"Details: {evidence_fail.details}")
    
    evidence_loop.close_node(task_node, evidence_fail)
    print(f"Node Status: {task_node.status}")
    
    if task_node.status == NodeStatus.FAILED:
        print("PASS: Node marked as FAILED.")
    else:
        print("FAIL: Node status not updated correctly.")

    print("\n--- [4] Testing Content Presence (TRUE) ---")
    task_node.status = NodeStatus.PENDING # reset
    task_node.verification_type = "content_presence"
    task_node.metadata["target_file"] = os.path.abspath("backend/core/ai_host/orchestration/evidence_loop.py")
    task_node.metadata["expected_content"] = "EvidenceLoop"
    
    evidence_content = evidence_loop.verify_node(task_node)
    print(f"Passed (Content 'EvidenceLoop'): {evidence_content.passed}")
    if evidence_content.passed:
        print("PASS: Content verified.")
    else:
        print("FAIL: Content not verified.")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(test_evidence_loop())
