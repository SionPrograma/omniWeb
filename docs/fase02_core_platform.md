# Fase 02 — Core Platform OmniWeb

Este documento detalla la implementación del núcleo básico de la plataforma modular OmniWeb, correspondiente a la Fase 02.

## Archivos Creados/Modificados

### 1. `backend/core/config.py` (Modificado)
- **Responsabilidad**: Gestionar la configuración central de la plataforma.
- **Cambios**: Se añadió `ACTIVE_MODULES`, una lista que define qué módulos deben cargarse al iniciar el backend. Actualmente incluye `["lingua"]`.

### 2. `backend/core/module_registry.py` (Existente, Integrado)
- **Responsabilidad**: Registro centralizado de módulos. Permite que el núcleo reconozca y conecte las rutas de cada módulo de forma dinámica (vía introspección de APIRouter).
- **Funcionamiento**: Expone un método `register_module` que inyecta los routers de los módulos en la aplicación principal de FastAPI.

### 3. `backend/core/event_bus.py` (Nuevo)
- **Responsabilidad**: Sistema de comunicación entre módulos basado en eventos (Pub-Sub).
- **Uso**: Permite que los módulos emitan señales (`emit`) y otros módulos reaccionen a ellas (`subscribe`) sin acoplamiento directo entre archivos.

### 4. `backend/main.py` (Modificado)
- **Cambios**: Se integró el bucle de registro automático para que recorra `ACTIVE_MODULES` de `config.py` y registre cada uno a través del `module_registry`.

## Cómo se registran los módulos

1. Se añade el nombre del módulo a la lista `ACTIVE_MODULES` en `backend/core/config.py`.
2. En `backend/main.py`, se asegura el mapeo correcto entre el nombre del módulo y su ruta de importación de Python.
3. El `module_registry` se encarga de importar dinámicamente el `router` e incluirlo en la aplicación FastAPI con el prefijo deseado.

## Siguiente paso recomendado

**Fase 03 — Interfaz de Administración y Estado**:
- Implementar un endpoint central en el core para consultar el estado de salud de todos los módulos registrados.
- Comenzar la integración de eventos reales entre el módulo `lingua` (emitiendo cuando un trabajo termina) y un futuro módulo de notificaciones o logs centralizado.
