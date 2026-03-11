# OmniWeb UI Core (Frontend Vanilla JS)

> **⚠️ AVISO ESTRUCTURAL IMPORTANTE:** 
> No confundir este directorio con `backend/core/`.
> Este directorio `core/` aloja **SÓLO** la lógica base Vanilla JS que se ejecuta en el navegador (browser) del cliente. No aloja servicios Python ni bases de datos.

Es la capa base del sistema para navegación, gestión de estado y almacenamiento compartido de toda la interfaz Multi-Page Application.

- `navigation/`: Gestiona la navegación global en el DOM entre chips (`nav-system.js`).
- `state/`: Gestor de estado en memoria para persistencia y restauración de sesiones de los chips (`state-manager.js`).
- `storage/`: Abstracción de `localStorage` / almacenamiento remoto para persistir datos localmente aislados.
- `shared/`: Recursos del cliente compartidos (CSS global base, utilitarios de formateo).
