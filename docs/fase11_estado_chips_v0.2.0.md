# Estado y Contrato del Sistema de Chips (OmniWeb v0.2.0)
ADR: Fase 2 - Consolidación Estructural

## 1. Inventario Real de Chips
Al momento de la versión 0.2.0, el ecosistema cuenta con los siguientes módulos de dominio:
- `chip-finanzas`
- `chip-idiomas-ia`
- `chip-musica`
- `chip-programacion`
- `chip-reparto`

## 2. Diferencias Estructurales Encontradas
- **Grupo Estándar (`finanzas`, `idiomas-ia`, `programacion`, `reparto`)**: Todos comparten la subcarpeta obligatoria `frontend/` (con `app.js`, `style.css`, `index.html`) e integran correctamente el `nav-system` y el `state-manager` de Vanilla JS provistos por el directorio raíz `core/`. Adicionalmente contienen subdirectorios vacíos o lógicos que segmentan sus dominios.
- **Grupo Placeholder (`chip-musica`)**: Tiene estructura lógica de carpetas (`/teoria`, `/practica`, etc.) e ideas (`README.md`), pero **carece** del subdirectorio funcional `frontend/`. No levanta UI.
- **Grupo Anómalo Transversal (`modules/lingua`)**: No es un chip, forma parte de un directorio legacy. Estructura monolítica separada con `api`, `services`, `models`, y un `ui` antiguo.

## 3. Contrato Mínimo de Chip v0.2.0
Para que una carpeta dentro de `chips/` sea considerada un Módulo Válido ("Estándar") en la v0.2.0, debe:
1. **Poseer Aislamiento Visual**: Toda su interfaz debe existir encapsulada dentro de la subcarpeta `frontend/`.
2. **Archivos Base (Vanilla)**: Incluir `index.html`, `style.css` y `app.js`.
3. **Integración con OmniCore**: El archivo `app.js` debe importar y auto-registrarse vía `import { navigation } from '/core/navigation/nav-system.js'` (llamando `navigation.navigateTo()`).
4. **Persistencia Delegada**: Los estados interactivos deben serializarse usando `stateManager.saveState()` de `/core/state/state-manager.js`.
5. **Autonomía**: Ningún chip invocará HTML/CSS de otros chips vecinos para prevenir acoplamiento ríspido.

## 4. Decisión Arquitectónica: modules/lingua vs chip-idiomas-ia
- **Decisión**: Se separan legalmente las responsabilidades. 
- **`chips/chip-idiomas-ia/`** asume la responsabilidad **Exclusiva y Estándar** de todo desarrollo visual y de UX orientado a lenguajes en el ecosistema. Es la interfaz oficial.
- **`modules/lingua/`** se conserva intacta pero se decreta como **Backend Legacy Transicional**. Su pesada arquitectura de transcripción y AI en Python servirá como proveedor de back-end a futuro.
- **Ejecución**: Se prohíbe tocar o borrar el Python robusto de `modules/lingua`. Todo nuevo esfuerzo front va a `chip-idiomas-ia`.

## 5. Clasificación del Sistema
### Estándar (Componentes Oficiales Activos)
- Frontend Shell (`frontend/dashboard/`)
- Módulo de Utilidades (`core/`)
- Orquestador API (`backend/main.py` y `backend/core/`)
- Chips Listos: `chip-reparto`, `chip-finanzas`, `chip-programacion`, `chip-idiomas-ia`.

### Legacy (Conservar en estado actual)
- Todo el ecosistema de código bajo `modules/` (como `lingua`, `assistant`, o `planner`), incluyendo sus UIs internas originales.

### Pendiente de Migración Futura (Documentar ahora, ejecutar después)
1. **Chip-Musica Frontend**: Construir y acoplar la carpeta `/frontend` y el `app.js` de navegación dentro de `chip-musica`.
2. **API Routing de Idiomas**: Mapear / abstraer los servicios de inferencia AI (Whisper, Groq) desde `modules/lingua/services/` hacia un nuevo router oficial interno en `chips/chip-idiomas-ia/api/`.
3. **Limpieza del Orquestador**: Retirar los `if module_name == "lingua"` incrustados en `/backend/main.py` que montaban la UI antigua, una vez terminada la absorción del backend al chip nuevo.
