from pydantic import BaseModel, Field
from typing import List, Optional

class ChipSpec(BaseModel):
    """
    Schema for generated chips.
    Matches ChipMetadata but with extra fields for the factory.
    """
    name: str
    slug: str
    type: str = "hybrid" # hybrid, frontend-only, utility
    description: str = "Módulo generado dinámicamente"
    permissions: List[str] = []
    endpoints: List[str] = [] # e.g. ["GET /notes", "POST /notes"]
    ui_components: List[str] = [] # future use for complex UIs

class SpecBuilder:
    """
    Converts a natural language intent or simple dict into a ChipSpec.
    """
    def build_from_intent(self, prompt: str) -> ChipSpec:
        # For now, we use a simple rule-based mapping.
        # In v1.0, this would call an LLM to extract fields.
        prompt = prompt.lower()
        
        name = "custom"
        if "notas" in prompt or "notes" in prompt:
            name = "notes"
        elif "contactos" in prompt or "contacts" in prompt:
            name = "contacts"
        elif "tareas" in prompt or "tasks" in prompt:
            name = "tasks"
            
        slug = f"custom-{name}"
        
        return ChipSpec(
            name=name.capitalize(),
            slug=slug,
            type="hybrid",
            description=f"Chip de {name} generado por OmniWeb Factory.",
            permissions=["db_access", "event_publish"],
            endpoints=[f"GET /{name}", f"POST /{name}"]
        )
