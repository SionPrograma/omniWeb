import logging
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.cluster.storage import storage_manager

logger = logging.getLogger(__name__)

class KnowledgeUnit(BaseModel):
    unit_id: str
    title: str
    type: str # concept, lesson, note, project, reference
    content: Optional[str]
    metadata: Dict[str, Any] = {}
    created_at: datetime

class KnowledgeStore:
    """
    Phase 30: Knowledge Storage Layer.
    Structured persistence on top of the Distributed Storage Grid.
    """
    async def ingest_knowledge(self, title: str, k_type: str, content: str, metadata: Dict[str, Any] = {}) -> str:
        # 1. Store in Grid Alexandria
        block_id = await storage_manager.store_data(
            data_type=f"knowledge_{k_type}",
            content=content.encode(),
            metadata=metadata
        )

        # 2. Register Unit
        unit_id = str(uuid.uuid4())
        query = """
        INSERT INTO knowledge_units (unit_id, title, type, content, block_id, metadata)
        VALUES (:uid, :title, :type, :content, :bid, :meta)
        """
        async with db_manager.get_session() as session:
            await session.execute(query, {
                "uid": unit_id, "title": title, "type": k_type,
                "content": content[:500], # Preview snippet
                "bid": block_id, "meta": metadata
            })
            await session.commit()
            
        logger.info(f"KnowledgeStore: Ingested {k_type} '{title}' ({unit_id})")
        return unit_id

    async def get_units(self, unit_type: Optional[str] = None) -> List[KnowledgeUnit]:
        query = "SELECT * FROM knowledge_units"
        if unit_type:
            query += " WHERE type = :type"
        
        async with db_manager.get_session() as session:
            res = await session.execute(query, {"type": unit_type})
            return [KnowledgeUnit(**dict(r)) for r in res]

knowledge_store = KnowledgeStore()
