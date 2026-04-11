# Plantilla de Chip Híbrido OmniWeb

Esta es la estructura oficial de referencia para crear nuevos módulos.

## Estructura de Archivos
* `chip.json`: Metadata y permisos requeridos.
* `core/router.py`: Puntos de entrada de la API (vía FastAPI).
* `core/service.py`: Lógica de negocio e integración.
* `core/repository.py`: Capa de persistencia (SQLite) con **carga diferida**.

## Reglas Críticas
1. **Soberanía**: Tu repositorio solo debe tocar sus propias tablas.
2. **Neutralidad**: No instancies conexiones a DB en el constructor o a nivel de módulo.
3. **Lazy Init**: Usa `_ensure_initialized()` antes de cualquier operación de datos.
4. **Contexto**: El sistema inyecta automáticamente el slug de tu chip para validar permisos.

Para más detalles, consulta: `/docs/ESTANDAR_SOBERANIA_CHIPS.md`
