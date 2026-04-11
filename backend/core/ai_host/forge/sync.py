import logging
import asyncio
from typing import List, Dict, Optional
from .affinity import forge_affinity_manager
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class ForgeCrossDomainSync:
    """
    V2.1: Cross-Domain Affinity Sync.
    Identifies high-transferability patterns across different chips/domains.
    """
    
    async def get_synergies(self, target_chip: str = "lingua") -> List[Dict]:
        """Retrieves candidate synergies for a specific target chip."""
        def _fetch():
            with db_manager.get_connection(internal=True) as conn:
                rows = conn.execute("""
                    SELECT * FROM intelligence_forge_cross_sync_advisories
                    WHERE target_chip = ? ORDER BY strength DESC
                """, (target_chip,)).fetchall()
                return [dict(r) for r in rows]
        return await asyncio.to_thread(_fetch)

    async def scan_for_synergies(self):
        """
        Scans all affinity memory for potential cross-domain patterns.
        (Simplified logic for V2.1 pilot: If Chip A has high affinity for Capability X,
        advise Chip B with similar needs.)
        """
        all_affinities = await forge_affinity_manager.get_affinities()
        
        # We find Strong Affinities (>0.5)
        strong_affs = [a for a in all_affinities if a['affinity_score'] > 0.5]
        
        synergies = []
        for aff in strong_affs:
            # For each strong affinity in Chip A, we look for 'comparable' Needs in Chip B.
            # (In V2.1, we demonstrate this by simulating 'vision' as a potential target).
            target_chips = ["vision", "lingua"] # lingua can sync with itself across capabilities? 
            for target in target_chips:
                if aff['chip_id'] == target: continue
                
                synergy = {
                    "source_chip": aff['chip_id'],
                    "target_chip": target,
                    "capability": aff['capability'],
                    "context_tag": aff['context_tag'],
                    "suggested_provider_id": aff['provider_id'],
                    "strength": aff['affinity_score'],
                    "rationale": f"Strong performance in {aff['chip_id']} suggest transferability for similar {aff['capability']} needs."
                }
                synergies.append(synergy)

        # Upsert synergies
        def _persist():
            with db_manager.get_connection(internal=True) as conn:
                for s in synergies:
                    conn.execute("""
                        INSERT OR REPLACE INTO intelligence_forge_cross_sync_advisories
                        (source_chip, target_chip, capability, context_tag, suggested_provider_id, strength, rationale)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (s['source_chip'], s['target_chip'], s['capability'], s['context_tag'], s['suggested_provider_id'], s['strength'], s['rationale']))
                conn.commit()
        
        await asyncio.to_thread(_persist)
        logger.info(f"Forge Synced {len(synergies)} cross-domain synergy candidates.")

# Global singleton 
forge_cross_sync = ForgeCrossDomainSync()
