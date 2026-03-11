# Arquitectura Modular OmniWeb (Arquitectura de Chips)

Este documento describe la nueva arquitectura base modular implementada en OmniWeb, siguiendo el concepto de "chips" funcionales.

## 1. Estructura Original
Previamente, el proyecto utilizaba una carpeta `modules/` para componentes específicos (como `lingua`) y una estructura de `backend/` y `frontend/` separada pero menos cohesionada.

## 2. Estructura Reutilizada
- Se ha mantenido el módulo `modules/lingua` por compatibilidad (Rule 2), pero se ha integrado lógicamente bajo el paraguas de `Idiomas IA`.
- Se ha actualizado el `backend/main.py` para soportar dinámicamente tanto la estructura legacy como la nueva estructura de chips.

## 3. Integración de Chip_Portable
No se encontró una carpeta llamada `chip_portable` en el directorio de trabajo actual. Se ha dejado preparada la carpeta `chips/chip-reparto/frontend` como destino para este componente una vez esté disponible, siguiendo el principio **PORTABLE FIRST / MAP OPTIONAL**.

## 4. Arquitectura Final Implementada

### Core System (`core/`)
- `navigation/`: Sistema de navegación global (`nav-system.js`).
- `state/`: Gestor de estado y persistencia local (`state-manager.js`).
- `storage/`: Capa de abstracción para datos persistentes.
- `shared/`: Recursos y estilos compartidos por todos los chips.

### Chips System (`chips/`)
Cada chip sigue una estructura modular estándar:
- **chip-reparto**: Logística con prioridad en interfaz portable.
- **chip-finanzas**: Gestión financiera (dashboards, ingresos, gastos).
- **chip-idiomas-ia**: Pipeline de aprendizaje (transcripción -> traducción -> salida).
- **chip-programacion**: Tutoría de arquitectura y software.
- **chip-musica**: Soporte teórico y práctico.

## 5. Preparación para Fases Futuras
- **Navegación**: Los chips pueden importar `core/navigation/nav-system.js` para gestionar el flujo de la aplicación.
- **Persistencia**: Se ha implementado el `state-manager.js` que permite el autoguardado de la sesión por cada chip.
- **Backend Modular**: `main.py` ahora registra automáticamente cualquier chip añadido a `settings.ACTIVE_MODULES` y monta su frontend estático.

---
*OmniWeb - Arquitectura de Chips v1.0*
