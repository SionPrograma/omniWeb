# Contrato Técnico de Chips (OmniWeb v1.0)

Este documento formaliza el estándar técnico para la creación, registro y mantenimiento de "Chips" (módulos independientes) dentro del ecosistema OmniWeb.

## 1. Clasificación de Chips

Un chip se categoriza según su nivel de integración con el backend:

| Categoría | Descripción | Requisito Mínimo | Ejemplo |
| :--- | :--- | :--- | :--- |
| **Hybrid Chip** | Posee interfaz visual y lógica de servidor propia. | `frontend/` + `core/router.py` | `chip-finanzas` |
| **Frontend-only** | Interfaz visual interactiva que usa persistencia local o APIs externas/legacy. | `frontend/` | `chip-programacion` |
| **Placeholder** | Definición lógica de dominio sin interfaz funcional aún. | `README.md` + Carpetas dominio | `chip-musica` |

## 2. Convenciones de Nomenclatura

*   **Identificador (Slug)**: `{nombre}` (ej. `reparto`, `finanzas`). Debe ser en minúsculas y sin espacios.
*   **Directorio raíz**: `chips/chip-{nombre}/`.
*   **Configuración**: El slug debe incluirse en `backend/core/config.py` dentro de `ACTIVE_MODULES`.
*   **Puntos de Acceso**:
    *   **UI**: Servida en `/{nombre}`.
    *   **API**: Servida en `/api/v1/{nombre}` (automático si existe router).

## 3. Estructura de Archivos Obligatoria

### Para UI (Frontend-only e Híbridos)
Todo chip funcional debe tener una carpeta `frontend/` con:
*   `index.html`: Estructura base. Debe incluir el `omni-shell`.
*   `app.js`: Punto de entrada de lógica. Debe importar `/core/`.
*   `style.css`: Estilos encapsulados.

### Para API (Solo Híbridos)
Si el chip requiere endpoints propios en FastAPI:
*   `core/router.py`: Debe exportar un objeto `router` de tipo `fastapi.APIRouter`.
*   **Requerimiento Python**: Tanto la raíz del chip (`chips/chip-{nombre}/`) como la carpeta `core/` deben contener un archivo `__init__.py` para permitir la importación dinámica.
*   **Nota**: El router no debe definir el prefijo `/api/v1/{nombre}`, ya que el `ModuleRegistry` lo inyecta dinámicamente.


## 4. Contrato de Comunicación con el Sistema (Core)

Los chips deben interactuar con el ecosistema a través de los módulos en `/core/`:

1.  **Navegación**:
    ```javascript
    import { navigation } from '/core/navigation/nav-system.js';
    navigation.navigateTo('chip-{nombre}'); // Registra la posición actual en el estado global.
    ```
2.  **Persistencia**:
    ```javascript
    import { stateManager } from '/core/state/state-manager.js';
    stateManager.saveState('chip-{nombre}', data);
    const data = stateManager.restoreState('chip-{nombre}');
    ```

## 5. Reglas de Oro
*   **Aislamiento**: Un chip no debe modificar el DOM de otro chip ni del Shell directamente.
*   **Resiliencia**: El frontend debe manejar la ausencia de backend (fallback a local) si se pierde la conexión.
*   **Independencia**: Los archivos en `chips/chip-A/` no deben importar nada de `chips/chip-B/` mediante rutas relativas.

## 6. Compatibilidad con el Cargador Dinámico
El archivo `backend/core/module_registry.py` detecta automáticamente el tipo de chip:
1.  Busca `chips/chip-{nombre}/frontend`. Si existe, monta el servidor de archivos estáticos.
2.  Busca `chips.chip-{nombre}.core.router`. Si existe, inyecta las rutas en la aplicación global bajo `/api/v1/{nombre}`.
3.  Si falla alguna importación de backend, el chip se considera "Frontend-only" y la carga continúa sin errores.
