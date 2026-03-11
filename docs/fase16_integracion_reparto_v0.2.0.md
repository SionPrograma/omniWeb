# Integración Chip-Reparto v0.2.0

## Objetivo
Implementar una integración real mínima viable entre el frontend de `chip-reparto` y el backend (FastAPI), manteniendo la compatibilidad con el sistema actual, asegurando un fallback local y siguiendo la filosofía "Portable First".

## Diagnóstico del Punto de Integración
- **Frontend actual:** Utiliza Vanilla JS (`app.js`) apoyado en estado local y datos mock (`defaultStops`). Ya dispone de un `stateManager` para persistencia en `LocalStorage`.
- **Backend actual:** Ya carga de manera dinámica los módulos registrados en `ACTIVE_MODULES` de `config.py`. En FastAPI se espera el router en el path `chips.chip-{modulo}.core.router`.
- **Decisión:** Habilitar un `router.py` ligero en `chips/chip-reparto/core/` que exponga las paradas almacenadas transicionalmente en memoria, lo que evita complicar la arquitectura con una base de datos prematura.

## Conexión Real Implementada
1. **Backend (`router.py` en `chip-reparto/core`):**
   - `GET /api/v1/reparto/stops`: Retorna la lista inicial de entregas.
   - `PUT /api/v1/reparto/stops/{stop_id}/status`: Permite actualizar el estado de una entrega.
   El backend almacena transicionalmente las modificaciones en una estructura de lista local en memoria, comportándose como una "pseuda-DB".

2. **Frontend (`app.js`):**
   - Actualizado el método `init()` para intentar hacer `fetch` a `/api/v1/reparto/stops`.
   - Si la consulta al backend falla, invoca inmediatamente el *fallback* con `stateManager` validando la persistencia y carga offline de manera segura.
   - En el método `changeStopStatus()`, se envía una solicitud `PUT` a la misma ruta. Se gestionan los errores silenciosamente a nivel de consola priorizando el registro de la acción en `stateManager` de forma que la UI y UX actual del usuario (Portable First) no se rompan nunca si no hay conexión al backend.

## Compatibilidad con el Sistema Actual
- **Sin reescrituras generalizadas:** Los cambios se centraron exclusivamente en incluir la inyección de `fetch` a la rutina existente, sin alterar variables globales ni flujo de navegación (se mantuvieron los IDs en el index.html y flujos de listado-detalle). No se tocó nada ajeno a `reparto`.
- **Fallback Activo:** El sistema puede funcionar sin que se levante Uvicorn de forma persistente a nivel frontend (portable first strategy).

## Pendientes / Documentar ahora, ejecutar después
- **Base de datos real:** Se decidió "documentar ahora, ejecutar después". Actualmente solo se muta memoria en la instancia de backend, no en disco / SQL.
- **Geolocalización / Componente de Mapa:** Se decidió no integrar todavía el flujo real de API Maps / backend. Se aplicará de forma progresiva.
- **Multi-tenant / Multi-usuario:** El estado guardado y recuperado por ahora es global a la sesión, no distinguido por conductor o repartidor autenticado.
