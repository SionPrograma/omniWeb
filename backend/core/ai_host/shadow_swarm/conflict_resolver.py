
import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
from .shadow_constructor import ShadowConstructor, ShadowConstructorProposal

logger = logging.getLogger(__name__)

class ConflictType(Enum):
    SAME_FILE_ZONE = "same_file_zone"          # Mismo archivo/zona
    CONTRACT_BREACH = "interface_contract"    # Firma de función incompatible
    PRECONDITION_FAIL = "precondition_broken"  # A invalida lo que B necesita
    UI_CORE_MISMATCH = "ui_logic_tension"     # Lógica vs Visual
    ORDER_DEPENDENCY = "execution_order"       # Dependencia circular o inversa

class ConflictSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ConflictRecord(BaseModel):
    shadow_ids: List[str]
    type: ConflictType
    severity: ConflictSeverity
    explanation: str
    resolution_strategy: str # priority, merge, sequence, discard

class ConflictResolver:
    """
    Detects and classifies technical/logical conflicts between multiple Shadow proposals.
    """
    
    def detect_conflicts(self, constructors: List[ShadowConstructor]) -> List[ConflictRecord]:
        conflicts = []
        proposals = [c for c in constructors if c.proposal]
        
        if len(proposals) < 2:
            return []

        # 1. FILE/ZONE CONFLICTS
        file_map = {}
        for c in proposals:
            f = c.proposal.target_file
            if f not in file_map: file_map[f] = []
            file_map[f].append(c)
            
        for file, consts in file_map.items():
            if len(consts) > 1:
                # Mismo archivo detectado
                conflicts.append(ConflictRecord(
                    shadow_ids=[c.shadow_id for c in consts],
                    type=ConflictType.SAME_FILE_ZONE,
                    severity=ConflictSeverity.HIGH,
                    explanation=f"Conflicto de escritura en '{file}': Múltiples Shadows intentan modificar el mismo archivo simultáneamente.",
                    resolution_strategy="sequence" # Ejecutar uno tras otro con re-audit
                ))

        # 2. LOGICAL TENSIONS (Simulated for this block)
        # Check if one is UI and another is Core and they touch related things
        ui_shadows = [c for c in proposals if "ui" in (c.target_layer or "").lower() or "frontend" in (c.target_file or "").lower()]
        core_shadows = [c for c in proposals if "core" in (c.target_layer or "").lower() or "backend" in (c.target_file or "").lower()]
        
        if ui_shadows and core_shadows:
            conflicts.append(ConflictRecord(
                shadow_ids=[ui_shadows[0].shadow_id, core_shadows[0].shadow_id],
                type=ConflictType.UI_CORE_MISMATCH,
                severity=ConflictSeverity.MEDIUM,
                explanation="Tensión UI vs Core: Cambio de lógica en el backend podría desincronizar el estado esperado por el frontend.",
                resolution_strategy="sequence"
            ))

        return conflicts

conflict_resolver = ConflictResolver()
