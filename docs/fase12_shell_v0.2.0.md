# Shell OmniWeb v0.2.0: Centro de Mando y Navegación
ADR: Fase 3 - Consolidación de Experiencia Inter-chip

## Contexto y Diagnóstico Previo
Antes de esta consolidación, la arquitectura basada puramente en MPA ocasionaba un desacoplamiento cognitivo severo desde el punto de vista del usuario (UX):
1. Cada vez que un usuario ingresaba a `chip-reparto` o `chip-finanzas`, se encontraba "atrapado" visualmente dentro de esa interfaz sin un cordón umbilical común de regreso a la aplicación madre, dependiendo forzosamente de los botones `Atrás` del navegador web o botones *hardcodeados*.
2. El Dashboard en `/frontend/dashboard/index.html` actuaba como una mera lista de anclajes pasivos, sin consciencia del quehacer del usuario en el sistema.

## Mejoras Implementadas en el Shell 

Las premisas innegociables fueron no convertir OmniWeb en una SPA, no añadir *React Router* y no tener que refactorizar el HTML individual de cada uno de los chips funcionales.

### 1. OmniDock Universal (Envoltorio MPA)
Se diseñó un interceptor universal de UI en `core/shared/components/omni-shell.js` (acompañado de `shell.css`) bautizado como **OmniDock**. 
- Esta pieza es injectada automáticamente desde la base del `nav-system.js` que todos los chips importan de por norma. 
- Muestra una pastilla o "dock" central fijo en la parte inferior de la pantalla.
- Al hacer clic, ejecuta un simple y seguro `window.location.href = '/'` para regresar al menú principal.
- Esto preserva 100% el modelo MPA (recargas limpias) brindando simultáneamente una sensación de "Sistema Operativo Personal" que acompaña persistente entre módulos.

### 2. Dashboard como Centro de Mando (Command Center)
Se ha dinamizado orgánicamente el HTML estático de entrada:
- Lee de manera nativa la memoria `omniweb_last_session` manejada por el `state-manager.js`.
- Al volver al hub general, ilumina inteligentemente en verde (mint/success) y remarca como "**Reciente**" aquél chip donde estuviste operando por última vez.

## Archivos Responsables
* `core/shared/components/omni-shell.js`: Componente inyector del botón de inicio maestro.
* `core/shared/styles/shell.css`: Estilos Glassmorphism en CSS Vanilla encapsulados.
* `core/navigation/nav-system.js`: Modificado para requerir e invocar este shell en cada inicialización de navegación de un chip.
* `frontend/dashboard/index.html`: Modificado añadiendo un detector post-carga nativo (`DOMContentLoaded`) responsable de aplicar los iluminados visuales recientes.

## Limitaciones Acordadas para Futuras Recurrentes
- **Colisiones Visuales:** Como los chips en CSS desconocen que una barra flotante ha sido instalada de repente en su pie de página (ya que se renderiza dinámicamente sobre ellos vía layout DOM global), componentes que floten en el centro/abajo de un macro-chip (como FAB de FAB o *alerts* en móvil) podrían chocar visualmente con el OmniDock. _(Documentar ahora, ejecutar parche de CSS/Padding general en la siguiente fase de refactor visual)_.
- **Falta de Notificaciones Globales:** El Dock actual solo contempla la navegación (Home). En fases futuras de backend se podría utilizar como host para un WebSocket transversal a fin de enviar mini notificaciones no intrusivas.
