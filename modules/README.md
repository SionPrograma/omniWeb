# Módulos Legacy (Pre-Chips v1.0)

> **⚠️ AVISO ESTRUCTURAL IMPORTANTE:** 
> Esta carpeta (`modules/`) marca el historial arquitectónico inicial del proyecto, cuando las funcionalidades de backend estaban estructuradas como `lingua`, `assistant`, `planner`, etc.
>
> **Bajo la Arquitectura v0.2.0, NO debes crear nuevos proyectos funcionales aquí.**

## Convención Actualizada (OmniWeb Chips)
La nueva convención del repositorio integra el *frontend y el backend asociado a dicho dominio* juntos dentro de la raiz directoria: `chips/chip-{nombre}/`.

### Estado de migración:
- El código en este directorio (como `lingua/api` o transciption logic) es todavía **altamente funcional** y valioso.
- La migración es **gradual y no destructiva**. Se mantiene aquí hasta que las funcionalidades internas sean absorbidas naturalmente como *routers/controladores backend* dentro del correspondiente `chips/chip-idiomas-ia/`, etc.
