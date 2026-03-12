import json
import os
from typing import Dict, Optional
from .logbook_models import Logbook

class LogbookStorage:
    def __init__(self, storage_dir: str = "data/logbooks"):
        self.storage_dir = storage_dir
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def save_logbook(self, logbook: Logbook):
        file_path = os.path.join(self.storage_dir, f"{logbook.owner_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(logbook.model_dump_json(indent=4))

    def load_logbook(self, owner_id: str) -> Optional[dict]:
        file_path = os.path.join(self.storage_dir, f"{owner_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

logbook_storage = LogbookStorage()
