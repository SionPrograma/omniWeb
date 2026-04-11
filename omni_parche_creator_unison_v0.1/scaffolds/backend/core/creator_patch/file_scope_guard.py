"""
File scope guard scaffold.

Purpose:
Prevent uncontrolled mutation when multiple agents/tools collaborate.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FileScopeLock:
    scope_id: str
    target_path: str
    range_hint: Optional[str] = None
    state: str = "proposed"


class FileScopeGuard:
    def acquire_lock(self, target_path: str, range_hint: Optional[str] = None) -> FileScopeLock:
        return FileScopeLock(scope_id=f"lock:{target_path}", target_path=target_path, range_hint=range_hint)

    def release_lock(self, lock: FileScopeLock) -> None:
        lock.state = "released"
