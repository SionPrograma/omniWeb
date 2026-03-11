# OmniWeb Chips (Arquitectura v1.0)
Estructura modular de funcionalidades ("chips") independientes. 

> **CONVENCIÓN ACTUAL:** Un **Chip** funge como la macro-aplicación principal de un micro-dominio operativo del ecosistema. Reemplazan el diseño legacy de `/modules/`.
>
> 1. Un chip es agnóstico o auto-contenido (`chip-{nombre}/frontend/` guarda la vista sin interferir con otros).
> 2. Interactúan con las bondades reusables centralizadas (`/core/state`, `/core/navigation`).
> 3. El servidor Backend (`backend/main.py`) lee qué chips deben ser servidos dinámicamente.

- `chip-reparto/`: Sistema de logística (Portable First, offline maps integration).
- `chip-finanzas/`: Control financiero personal, calculadoras dinámicas y ahorros.
- `chip-idiomas-ia/`: Tutor de idiomas bilingüe asistido por inteligencia contextual.
- `chip-programacion/`: Mentoría interactiva de desarrollo, arquitecturas y patrones.
- `chip-musica/`: Gestión de teoría práctica e improvisación.
