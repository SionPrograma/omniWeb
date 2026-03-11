# Arquitectura del Backend Modular (ModuleRegistry)

OmniWeb utiliza un orquestador centralizado para gestionar el ciclo de vida de los chips. Esta lógica reside en `backend/core/module_registry.py` y sigue un patrón de tres etapas bien diferenciadas.

## 1. El Ciclo de Registro

Cuando el servidor arranca, recorre los chips habilitados y ejecuta el siguiente flujo para cada uno:

### A. Descubrimiento (Discovery)
- **Metadata**: Se busca el archivo `chip.json` para obtener el nombre real, versión y visibilidad.
- **Backend**: Se intenta localizar un objeto `APIRouter` de FastAPI siguiendo dos convenciones de importación (módulo directo o archivo `router.py`).
- **Resiliencia**: Si no se encuentra backend, el sistema lo marca como `frontend-only` sin fallar.

### B. Validación (Validation)
- Se verifica que el objeto descubierto sea efectivamente una instancia de `fastapi.APIRouter`.
- Se validan dependencias críticas; si el código del chip falla por falta de librerías internas, se registra el error explícitamente.

### C. Montado (Mounting)
- El router validado se inyecta en la aplicación principal de FastAPI.
- Se le asigna el prefijo correspondiente (ej: `/api/v1/finanzas`).
- Se actualiza el estado interno del registro para que el Dashboard pueda descubrirlo.

## 2. Métodos Privados y Responsabilidades

| Método | Responsabilidad | Descripción |
| :--- | :--- | :--- |
| `_load_metadata` | Discovery | Carga declarativa desde `chip.json`. |
| `_discover_backend_router` | Discovery | Localización del código Python. |
| `_validate_backend` | Validation | Chequeo de contrato técnico (APIRouter). |
| `_mount_backend_router` | Mounting | Integración física en la app FastAPI. |
| `_register_module_state` | State | Persistencia en memoria del inventario de chips. |

## 3. Ventajas de esta Estructura
1.  **Escalabilidad**: Es fácil añadir nuevas reglas de validación sin tocar la lógica de montado.
2.  **Depuración**: Los errores se capturan en la etapa exacta donde ocurren (ej: falla de importación vs falla de montado).
3.  **Agnosticismo**: El registro no necesita saber *qué* hace el chip, solo *cómo* conectarlo.
