import asyncio
import sys
import os
from sqlalchemy import text

sys.path.append(r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb")

async def test_scaling_compat():
    from backend.core.database import db_manager
    from backend.core.permissions import set_chip_context
    
    print("--- Testing SQLAlchemy-like compatibility (mappings().all()) ---")
    try:
        with set_chip_context("core"):
            async with db_manager.get_session() as session:
                # Test with SQLAlchemy text object
                query = text("SELECT 1 as val, 'test' as name")
                res = await session.execute(query)
                
                # Test mappings().all()
                rows = res.mappings().all()
                print(f"Rows: {rows}")
                if rows[0]["val"] == 1 and rows[0]["name"] == "test":
                    print("PASS: mappings().all() and text() compatibility working.")
                else:
                    print("FAIL: Result data mismatch.")
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scaling_compat())
