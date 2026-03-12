import uuid
from typing import List, Dict, Optional
from datetime import datetime
from .logbook_models import Logbook, LogbookEntry, EntryType, LogbookConnection, ConnectionType

class LogbookManager:
    def __init__(self):
        self.logbooks: Dict[str, Logbook] = {}  # owner_id: Logbook

    def get_or_create_logbook(self, owner_id: str, owner_name: str = "Anonymous") -> Logbook:
        if owner_id not in self.logbooks:
            self.logbooks[owner_id] = Logbook(
                id=str(uuid.uuid4()),
                owner_id=owner_id,
                owner_name=owner_name
            )
        return self.logbooks[owner_id]

    def add_entry(self, owner_id: str, entry_type: EntryType, content: any, tags: List[str] = []) -> Optional[LogbookEntry]:
        logbook = self.get_or_create_logbook(owner_id)
        entry = LogbookEntry(
            id=str(uuid.uuid4()),
            type=entry_type,
            content=content,
            tags=tags
        )
        logbook.entries.append(entry)
        logbook.last_updated = datetime.now()
        
        # Automatic topic extraction from tags
        for tag in tags:
            if tag not in logbook.knowledge_topics:
                logbook.knowledge_topics.append(tag)
                
        return entry

    def update_skill(self, owner_id: str, skill_name: str, level: float):
        logbook = self.get_or_create_logbook(owner_id)
        logbook.skills[skill_name] = max(0.0, min(1.0, level))
        logbook.last_updated = datetime.now()

    def connect_logbooks(self, owner_id: str, target_owner_id: str, conn_type: ConnectionType):
        logbook_a = self.get_or_create_logbook(owner_id)
        logbook_b = self.get_or_create_logbook(target_owner_id)
        
        # Add connection to A
        if not any(c.target_logbook_id == logbook_b.id for c in logbook_a.connections):
            logbook_a.connections.append(LogbookConnection(target_logbook_id=logbook_b.id, type=conn_type))
            
        # Add connection to B
        if not any(c.target_logbook_id == logbook_a.id for c in logbook_b.connections):
            logbook_b.connections.append(LogbookConnection(target_logbook_id=logbook_a.id, type=conn_type))

    def get_logbook_by_id(self, logbook_id: str) -> Optional[Logbook]:
        for lb in self.logbooks.values():
            if lb.id == logbook_id:
                return lb
        return None

logbook_manager = LogbookManager()
