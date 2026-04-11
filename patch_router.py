import sys
import os

router_path = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb\backend\core\governance\router.py"

with open(router_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """@router.get("/wisdom/atlas/node/{node_id}")
async def get_wisdom_atlas_node_detail(node_id: str, admin_user: OmniUser = Depends(get_admin_user)):
    \"\"\"Returns details and connected evidence for a specific wisdom node.\"\"\"
    from backend.core.governance.atlas_engine import atlas_engine
    nodes = atlas_engine.get_nodes()
    node = next((n for n in nodes if n.node_id == node_id), None)
    if not node:
        raise HTTPException(status_code=404, detail="Atlas Node not found.")
    return {"status": "success", "payload": node.model_dump()}"""

replacement = """@router.get("/wisdom/atlas/node/{node_id}")
async def get_wisdom_atlas_node_detail(node_id: str, admin_user: OmniUser = Depends(get_admin_user)):
    \"\"\"Returns details and connected evidence for a specific wisdom node.\"\"\"
    from backend.core.governance.atlas_engine import atlas_engine
    nodes = atlas_engine.get_nodes()
    node = next((n for n in nodes if n.node_id == node_id), None)
    if not node:
        raise HTTPException(status_code=404, detail="Atlas Node not found.")
    
    # Enrichment
    payload = node.model_dump()
    payload["sync_history"] = atlas_engine.get_node_sync_history(node_id)
    return {"status": "success", "payload": payload}"""

if target in content:
    new_content = content.replace(target, replacement)
    with open(router_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replacement success.")
else:
    print("Target not found.")
    # Show snippet of what we found to debug
    idx = content.find('@router.get("/wisdom/atlas/node/{node_id}")')
    if idx != -1:
        print(f"Found something at {idx}:")
        print(content[idx:idx+300])
