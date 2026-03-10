# Fase 04 — Dashboard Visual (Spatial UI)

Este documento describe la implementación de la primera interfaz visual de OmniWeb, inspirada en una visión futura de entornos AR/VR con módulos flotantes (chips).

## 🚀 Objetivo
Crear una interfaz ligera y estética que sirva como punto de entrada central para todos los módulos de OmniWeb, manteniendo la simplicidad técnica (sin frameworks pesados).

## 📂 Archivos Creados/Modificados

### 1. `frontend/dashboard/index.html`
- **Interfaz Principal**: Contiene el HTML, CSS y JavaScript necesario para el dashboard.
- **Estética Espacial**: 
  - Fondo oscuro con gradiente radial.
  - Generación dinámica de estrellas mediante JavaScript para dar profundidad.
  - Efecto de "glassmorphism" en los chips.
- **Interactividad**:
  - Animación de flotación suave mediante CSS.
  - Efecto de profundidad (paralaje) que reacciona al movimiento del mouse.
  - Navegación directa al módulo `Lingua`.

### 2. `backend/main.py`
- **Modificación**: Se cambió el endpoint raíz (`/`) para que devuelva el archivo `index.html` del dashboard en lugar de un JSON de bienvenida.
- **Servicio**: Utiliza `FileResponse` de FastAPI para servir el archivo estático de forma eficiente.

## 🛠️ Cómo funciona el Dashboard

### Chips Flotantes
Cada módulo se representa como un "chip" con las siguientes características:
- **Activos**: Chips que dirigen a una ruta funcional (ej. `Lingua` -> `/lingua/`).
- **Próximamente (Coming Soon)**: Chips visuales que representan módulos planeados para el futuro (`Planner`, `Nutrition`, `Assistant`), con una opacidad reducida y sin interacción de click.

### Animaciones
- **Flotación**: Se utilizan `keyframes` de CSS (`@keyframes float`) con diferentes duraciones y retrasos (`animation-delay`) definidos mediante variables CSS inline para cada chip, logrando un movimiento orgánico.
- **Profundidad 3D**: Un pequeño script de JavaScript escucha el evento `mousemove` y rota ligeramente el contenedor de los chips, simulando un entorno holográfico en 3D.

## ➕ Cómo agregar nuevos Chips

Para agregar un nuevo módulo al dashboard:

1. Abre `frontend/dashboard/index.html`.
2. Dentro de `<main class="chips-container">`, añade un nuevo bloque:

```html
<!-- Ejemplo: Nuevo Módulo -->
<a href="/nuevo-modulo/" class="chip active" style="--float-duration: 6s; --float-delay: 0.2s;">
    <span class="chip-title">Nuevo</span>
    <span class="chip-status">Active</span>
</a>
```

3. Si el módulo aún no está listo, usa la clase `coming-soon` y un `div` en lugar de una etiqueta `a`.

## 🔗 Conexión de Chips Futuros

A medida que se desarrollen los nuevos módulos (`Planner`, `Nutrition`, etc.):
1. Los módulos deben seguir el patrón de `Lingua` y ser montados en `backend/main.py` usando `StaticFiles` o sus propios routers.
2. Una vez montados, el chip correspondiente en el dashboard debe actualizarse de `div.coming-soon` a `a.active` con el enlace correcto.
