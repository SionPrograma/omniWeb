# Release Notes - OmniWeb v0.3.0 🚀

## Resumen del Proyecto
OmniWeb v0.3.0 marca el paso de un sistema MPA dinámico a una infraestructura **persistente y profesional**. Esta versión consolida el "Corazón" de la plataforma, permitiendo que los módulos (Chips) gestionen datos reales de forma segura, portátil y desacoplada.

## 🌟 Logros Principales de esta Versión

1.  **Persistencia Definitiva (SQLite)**:
    - Implementación de un motor de datos centralizado en `backend/data/omniweb.db`.
    - Eliminación de la dependencia de "Mock DBs" en memoria para los procesos críticos.
    - Soporte para transacciones seguras y acceso por nombre de columna (Row Factory).

2.  **Arquitectura S.R.S.R (Backend por Chip)**:
    - Estándar de 4 capas: **Schemas, Repository, Service y Router**.
    - Desacoplamiento total entre la lógica de negocio y el transporte HTTP.
    - Migración completa de los chips `finanzas` y `reparto` a este nuevo patrón.

3.  **ModuleRegistry Inteligente**:
    - Lifecycle de carga separado: *Discovery -> Validation -> Mounting*.
    - Detección automática de dependencias rotas antes de inyectar rutas a FastAPI.
    - Registro pasivo de chips frontend-only y placeholders.

4.  **Dashboard Dinámico**:
    - Generación automática de UI basada en metadata real escaneada del sistema.
    - Nueva API de sistema `/api/v1/system/chips` para el autodescubrimiento de módulos.

## 🏗 Arquitectura del Sistema (v0.3.0)

OmniWeb opera como una **Plataforma MPA Híbrida**:
- **Core**: Orquestador FastAPI y utilidades Vanilla JS (Shell, Nav, State).
- **Persistence**: SQLite centralizado.
- **Modules**: "Chips" independientes bajo el estándar v1.0.

## 🔋 Estado de los Chips

| Chip | Estado v0.3.0 | Características Clave |
| :--- | :--- | :--- |
| **Finanzas** | ✅ Persistente | S.R.S.R, SQLite, Relative Imports. |
| **Reparto** | ✅ Persistente | Auto-seeding de datos, SQLite, Portable-First. |
| **Idiomas-IA** | ⏹️ Frontend Ready | UI consolidada, listo para integración de LLM. |
| **Lingua** | 🕰️ Legacy | Backend IA activo, UI depreciada. |
| **Programación**| ⏹️ Frontend Ready | Layout y Simulación IDE. |
| **Música** | ⏳ Placeholder | Estructura de carpetas definida. |

## 🚀 Roadmap Futuro
- **v0.4.0**: Integración real con LLMs (Local/Remote) en el chip de Idiomas.
- **Sistema de Bus de Eventos**: Comunicación inter-chip en el backend.
- **Identity & Auth**: Soporte multicuenta para la plataforma personal.
- **PWA Enhancement**: Mejorar las capacidades offline del Shell global.

---
**OmniWeb v0.3.0 está listo para ser publicado en el entorno de producción local.**
