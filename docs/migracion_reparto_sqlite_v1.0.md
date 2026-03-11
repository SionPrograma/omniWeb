# Migración de Reparto a SQLite (v1.0)

Este documento registra la migración del chip de reparto desde almacenamiento volátil en memoria hacia persistencia definitiva con SQLite.

## 1. Diagnóstico del Estado Previo

El chip `chip-reparto` almacenaba los estados de las paradas (ENTREGADO, PENDIENTE, AUSENTE) en una lista global de Python. 
- **Volatilidad**: Al reiniciar el servidor, todas las entregas volvían a estado "PENDIENTE".
- **Falta de Semillas**: No existía un mecanismo para garantizar datos iniciales de forma consistente en el backend.

## 2. Implementación Realizada

Se ha completado la migración siguiendo el patrón **S.R.S.R** y los principios del proyecto:

### Backend (SQLite)
- **Repositorio (`repository.py`)**: Implementa `init_db()` que no solo crea la tabla `stops`, sino que inserta automáticamente las 4 paradas base si la base de datos está vacía.
- **Servicio (`service.py`)**: Encapsula las operaciones de lectura y actualización.
- **Router (`router.py`)**: Conecta con los procedimientos del servicio utilizando importaciones relativas para garantizar estabilidad.

### Estética y UX (Portable First)
- Se ha mantenido el enfoque **Portable First / Map Optional**. El sistema sigue funcionando perfectamente sin necesidad de capas geográficas complejas.
- El frontend gestiona la sincronización mediante `fetch` pero mantiene el `localStorage` (vía `stateManager`) como fallback de resiliencia si la red falla.

## 3. Preservación de Compatibilidad

Se han mantenido intactos los contratos API:
- `GET /api/v1/reparto/stops`: Retorna el objeto `{"stops": [...]}` que el frontend espera.
- `PUT /api/v1/reparto/stops/{id}/status`: Recibe el JSON `{"status": "..."}`.

Esto garantiza que el archivo `frontend/app.js` funcione sin una sola línea de modificación.

## 4. Validación de Persistencia
Cualquier cambio de estado realizado desde la aplicación web ahora se guarda permanentemente en `backend/data/omniweb.db`. El reinicio del servidor ya no provoca la pérdida del progreso de la jornada de reparto.
