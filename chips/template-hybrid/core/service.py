from .repository import template_repo

class TemplateService:
    def get_system_status(self):
        # Lógica de negocio
        data = template_repo.get_data()
        return {"status": "ok", "data_count": len(data)}

template_service = TemplateService()
