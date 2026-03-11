# Contrato Mínimo de Chips (OmniWeb v0.2.0)
ADR-002: Definición del Estándar de Módulo

## Contexto
Para evitar que cada macro-aplicación (chip) se construya con interfaces, lógicas de navegación o persistencia totalmente dispares, es imperativo establecer un contrato mínimo realista basado en el código ya funcional en el repositorio. Este contrato dicta qué convierte a una carpeta dentro de `chips/` en un verdadero "Chip OmniWeb".

## El Contrato Estándar v0.2.0
Todo nuevo chip en `chips/chip-{nombre}/` debe contar, como mínimo, con la siguiente estructura y comportamiento:

### Estructura de Directorios Clave
- `frontend/`: Directorio obligatorio que aloja la interfaz visual pura. FastApi lo montará automáticamente en `/{nombre}`.
  - `index.html`: Documento HTML estructural.
  - `style.css`: Estilos en Vanilla CSS.
  - `app.js`: Script de lógica de UI interactiva en Vanilla JS.

### Reglas de Integración (app.js)
El archivo `app.js` debe obligatoriamente importar el Core JS y auto-registrarse:
1. **Importación:** 
   ```javascript
   import { navigation } from '/core/navigation/nav-system.js';
   import { stateManager } from '/core/state/state-manager.js';
   ```
2. **Registro de Navegación:** Durante su inicialización (ej. función `init()`), debe invocar:
   ```javascript
   navigation.navigateTo('chip-nombre');
   ```
3. **Persistencia (Autoguardado):** Todo cambio significativo en el estado vivo de la UI debe guardarse usando:
   ```javascript
   stateManager.saveState('chip-nombre', estadoGral);
   ```
4. **Restauración de Sesión:** Durante el montado de la vista, debe intentar recuperar el progreso anterior de forma resiliente:
   ```javascript
   const savedState = stateManager.restoreState('chip-nombre');
   ```
5. **Aislamiento Cero Fricción:** Ningún chip debe invocar selectores DOM (ej. `document.getElementById`) o IDs que pertenezcan a otros chips. 

## Estado Actual Acorde al Contrato
- ✅ Cumplen íntegramente: `chip-reparto`, `chip-finanzas`, `chip-programacion`, `chip-idiomas-ia`.
- ⚠️ Pendientes front/design: `chip-musica`.

## Relación con Legacy APIs (Caso `modules/`)
El orquestador `backend/main.py` está preparado para cargar Chips por convención de nombres de carpetas.
Las APIs escritas bajo `modules/` (ej. `lingua/api`) forman parte del pasado del proyecto. Un chip que requiera backend actualmente tendrá la libertad de integrar su propia subcarpeta `api/` o conectarse a dichas lógicas legacy hasta que estas migren iterativamente a sus respectivos chips.
