# Especificación de Metadata de Chips (chip.json)

OmniWeb utiliza un sistema de metadata declarativa y opcional para facilitar el autodescubrimiento y la orquestación dinámica de chips.

## 1. El Archivo `chip.json`

Cada chip puede incluir un archivo `chip.json` en su raíz (`chips/chip-{slug}/chip.json`). Este archivo define las propiedades públicas y técnicas del módulo.

## 2. Esquema de Metadata

### Campos Obligatorios (Recomendados para registro formal)
- `id` (string): Identificador único del chip (ej: `chip-finanzas`).
- `slug` (string): Identificador simplificado usado en rutas y config (ej: `finanzas`).
- `name` (string): Nombre legible para mostrar en el Dashboard (ej: `Finanzas`).

### Campos Opcionales
- `description` (string): Breve explicación de la funcionalidad del chip.
- `version` (string): Versión semántica del chip.
- `type` (enum): Categoría del chip. Valores sugeridos: `hybrid`, `frontend-only`, `placeholder`.
- `has_frontend` (boolean): Indica si el chip sirve una interfaz visual.
- `has_backend` (boolean): Indica si el chip registra rutas en el router de FastAPI.
- `entry_frontend` (string): Ruta al archivo principal de entrada (ej: `frontend/index.html`).
- `dashboard_visible` (boolean): Controla si el chip debe aparecer en el Dashboard principal.

## 3. Ejemplo Relevante

```json
{
  "id": "chip-finanzas",
  "slug": "finanzas",
  "name": "Finanzas",
  "description": "Gestión personal de movimientos financieros con soporte híbrido",
  "version": "0.2.1",
  "type": "hybrid",
  "has_frontend": true,
  "has_backend": true,
  "entry_frontend": "frontend/index.html",
  "dashboard_visible": true
}
```

## 4. Estrategia de Fallback

El sistema está diseñado para ser resiliente. Si un chip NO posee `chip.json`:

1.  **Nombre**: Se utiliza el slug capitalizado (ej: `Reparto` para `reparto`).
2.  **Estado**: El `ModuleRegistry` deduce si es `active` o `frontend-only` basándose en la existencia de `core/router.py`.
3.  **Metadata**: El objeto `metadata` en el registro interno contendrá solo lo básico (`name` y `slug`).

## 5. Integración con el Sistema

La metadata es leída durante el arranque del servidor por `backend/core/module_registry.py` y puede ser consumida a través de `module_registry.get_active_modules()`. Esto permite que el Dashboard se genere dinámicamente consultando estas propiedades.
