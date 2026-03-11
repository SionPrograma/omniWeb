# Nueva UI Chip-Reparto: Map-First + Operations Drawer

Este documento describe la fusión de la interfaz de mapa portable (Referencia 2) con el panel operativo de OmniWeb (Referencia 1).

## Estructura Visual
1. **Mapa (Lienzo Principal):**
   - El mapa de Leaflet ocupa el 100% de la pantalla.
   - Sigue la configuración de la referencia portable (modo gris/color).
2. **Operations Drawer (Panel Lateral):**
   - Panel desplegable a la derecha que contiene la lógica operativa de OmniWeb.
   - Incluye: Listado de paradas, detalles de parada, acción masiva y chat local.
   - Estados: `open` y `closed` con animación CSS.
3. **Navegación Superior:**
   - Conserva el botón de retroceso y el título de OmniWeb.
   - Estética translúcida para integración visual con el mapa.

## Implementación Técnica
- **Stack:** HTML, CSS y Vanilla JS.
- **Librerías:** Leaflet @1.9.4 (CDN).
- **Core:** Mantiene el uso de `nav-system.js` y `state-manager.js`.
- **Interacción:**
  - Clic en marcador -> Abre detalle en Drawer.
  - Clic en lista -> Centra mapa en marcador.
  - Cambio de estado -> Sincroniza visualmente marcador y lista.
