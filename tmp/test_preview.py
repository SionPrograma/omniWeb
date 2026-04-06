import asyncio
import sys

sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')

from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
import backend.core.permissions

def mock_enforce(perm): return True
backend.core.permissions.enforce_permission = mock_enforce

async def test_preview():
    print("\n--- DOMAIN REBASE PREVIEW STRESS TEST ---")
    
    # 1. Fetch macro
    macro = roadmap_aggregator.get_macro_roadmap()
    if not macro.groups:
        print("No groups found. Run test_readiness.py first to populate data.")
        return

    # 2. Generate Preview for a group (e.g. backend or auth)
    for g in macro.groups:
        sid = g.group_id.replace('surface_', '')
        print(f"\nGENERING PREVIEW FOR: {sid.upper()}")
        try:
            plan = roadmap_aggregator.get_domain_preview(g.group_id)
            print(f" - Domain: {plan.domain_name}")
            print(f" - Feasibility: {plan.atomic_feasibility}")
            print(f" - Items: {len(plan.items)}")
            for item in plan.items:
                print(f"   [{item.sequence_index}] {item.title[:30]} | Rebase: {item.rebase_needed} | Blocks: {item.governance_blocks}")
            print(f" - Critical Blockers: {plan.critical_blockers}")
            print(f" - Next Steps: {plan.next_steps}")
        except Exception as e:
            print(f" - Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_preview())
