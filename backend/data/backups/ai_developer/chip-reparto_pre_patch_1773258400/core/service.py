from typing import List, Optional
import requests
import logging
from .repository import reparto_repo
from .schemas import Stop

logger = logging.getLogger(__name__)

class RepartoService:
    """
    Business logic layer for chip-reparto.
    Handles geocoding for stops missing coordinates.
    """
    def __init__(self):
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        self.user_agent = "OmniWeb-Reparto/1.0 (contact: your-email@example.com)"

    def get_all_stops(self) -> List[Stop]:
        stops = reparto_repo.get_all()
        
        # Incremental Geocoding: solo si faltan coordenadas
        for stop in stops:
            if stop.lat is None or stop.lng is None:
                coords = self.geocode_address(stop.address)
                if coords:
                    stop.lat, stop.lng = coords
                    reparto_repo.update_coordinates(stop.id, stop.lat, stop.lng)
                    logger.info(f"Geocoded stop {stop.id}: {coords}")
        
        return stops

    def geocode_address(self, address: str) -> Optional[tuple]:
        """Llamada ligera a Nominatim (OSM)."""
        try:
            params = {
                "q": address,
                "format": "json",
                "limit": 1
            }
            headers = {"User-Agent": self.user_agent}
            response = requests.get(self.nominatim_url, params=params, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"])
            return None
        except Exception as e:
            logger.warning(f"Geocoding failed for {address}: {e}")
            return None

    def update_delivery_status(self, stop_id: int, status: str) -> Optional[Stop]:
        return reparto_repo.update_status(stop_id, status)

# Global instance
reparto_service = RepartoService()
