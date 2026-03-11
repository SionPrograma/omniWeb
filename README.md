# OmniWeb 🌐
**Version:** v0.2.0

OmniWeb es un **Sistema Operativo Personal Web** en fase de desarrollo activo. Fue diseñado para centralizar y orquestar múltiples servicios, aplicaciones y dominios de conocimiento (finanzas, aprendizaje, gestión de ideas) bajo un único ecosistema digital ligero y unificado.

El enfoque técnico principal del proyecto es proveer un portafolio de arquitectura robusta, priorizando el agnosticismo de frameworks de frontend y el crecimiento incremental seguro por encima del sobre-diseño (*over-engineering*).

## 🏗 Arquitectura (v0.2.0)

OmniWeb rompe deliberadamente con la tendencia predominante de las *Single Page Applications* (SPA) monolíticas en React o Vue. En su lugar, opera como una **Multi-Page Application (MPA)** híbrida:

1. **Backend Orquestador (FastAPI)**: El núcleo Python actúa como servidor de recursos, inyectando de forma dinámica las aplicaciones (Chips) activas en el sistema sin necesidad de refactorizar el enrutador cada vez que nace un módulo nuevo.
2. **"Chips" (Dominios Aislados)**: Las micro-aplicaciones (`chip-finanzas`, `chip-reparto`, etc.) conviven en carpetas estancas. Una caída o error crítico en el chip de Finanzas no rompe el chip de Programación.
3. **Frontend Vanilla First**: La interfaz está construida estrictamente con HTML, Vanilla CSS y Vanilla JS (Módulos ES6). Esto garantiza carga inmediata, cero fricción de build, e inmunidad absoluta a *Dependency Hell*.
4. **OmniDock Shell (Interoperabilidad)**: Un inyector global superpone de manera dinámica un botón *Glassmorphism* y lógicas de sistema transversal a través de todas las aplicaciones locales, proveyendo cohesión al usuario sin acoplar el código DOM de los diferentes chips.

## 🗂 Estructura de Proyecto

OmniWeb exige un respeto estricto a las responsabilidades por directorio:

- `backend/`: Código Python del servidor.
  - `backend/core/`: **Backend Core**. Configuración (`config.py`) y registro automático de módulos (`module_registry.py`).
  - `backend/main.py`: Punto ciego de entrada. Sirve los frontends dinámicamente.
- `core/`: **Frontend Core**. Librería de Vanilla JS del sistema. Contiene `nav-system` (Navegación MPA), `state-manager` (Persistencia del cliente) y el `omni-shell`.
- `frontend/dashboard/`: UI espacial del "Centro de Mando" global. Se sirve en la ruta raíz (`/`). No contiene apps, sólo orquesta el acceso mediante lecturas inteligentes del progreso reciente.
- `chips/`: El estándar activo para crear módulos.
- `modules/`: Código **Legacy**. Alberga servicios complejos, pesados o transicionales desarrollados en las fases pre-chips de OmniWeb (Servicios Pydantic, Whisper AI, inferencias).

## 🔋 Estado Actual del Ecosistema (v0.2.0)

### 📌 Implementado y Estándar
- **Dashboard Central**: Activo. Realiza tracking inteligente mediante el `state-manager` para resaltar de qué chip provino el usuario.
- **Chip Finanzas**: Activo. Interfaz *Mobile-friendly* para gastos e ingresos.
- **Chip Reparto**: Activo. Prototipo híbrido de mapa e iteraciones PWA.
- **Chip Programación**: Activo. IDE simulado y layout lateral.
- **Chip Idiomas IA**: Activo. Interfaz visual consolidada para el futuro mentor bilingüe.

### 🕰️ Legacy y Transicional (Uso Restringido)
- **Lingua (`modules/lingua`)**: Es el backend poderoso en Python que orquesta IA de voz pero cuyo Front original ya no condice con la arquitectura. Su uso visual está **depreciado**.

### 🔭 Roadmap y Visión Futura (Documentado, Ejecución Pendiente)
- **Persistencia en Base de Datos**: Actualmente, OmniWeb v0.2.0 delega responsablemente el guardado de sesiones temporales y progresos al `LocalStorage` o `SessionStorage` puro de cada componente a fin de no bloquear la creación de UI. En el futuro, el orquestador FastApi abrirá endpoints de resguardo persistente.
- **Migración de Backend de IA**: Extraer los endpoints asíncronos y rutinas LLM pesadas que viven apagadas hoy en `modules/lingua/services` e inyectarlas dentro de la api oficial del `chips/chip-idiomas-ia/api/`.
- **Chip Música**: En estado de *Placeholder*. Existe organización de ideas lógicas pero falta desarrollar su interfaz visual.
- **Multiusuario & Identidad**: Hoy la plataforma es intrínsecamente monousuario (pensada como herramienta personal del desarrollador). A futuro, implementará _Auth_ centralizado.

## 📖 Documentación Interna (ADRs)

Todo gran salto arquitectural se encuentra metódicamente trazado en la carpeta `docs/`. Destacan para esta versión:
- `fase08_arquitectura_v0.2.0.md` ⇨ Separación Frontend/Backend en entorno Vanilla MPA.
- `fase09_contrato_chips_v0.2.0.md` ⇨ Qué condiciones exige el ecosistema para que una app cuente como "Chip".
- `fase12_shell_v0.2.0.md` ⇨ Integración de UX global sin utilizar React Routers.
