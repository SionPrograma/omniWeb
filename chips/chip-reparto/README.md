# Chip Reparto

Este chip gestiona la logística de reparto y entregas. Cumple con el principio de **PORTABLE FIRST / MAP OPTIONAL**, garantizando que el flujo principal operativo dependa completamente de listas e interacciones manuales, siendo el mapa un apoyo visual prescindible si falla.

## Estructura del Chip

1. **`core/`**: Contiene la lógica de negocio profunda específica del reparto (cálculo de distancias, optimización de rutas o API de sincronización pesada). (Actualmente vacío/preparado).
2. **`frontend/`**: Interfaz de usuario "Portable". Muestra la lista de entregas, permite cambiar los estados (Pendiente, Entregado, Ausente) e implementa la navegación simple entre la vista principal (lista) y la vista de detalle. Es el corazón operativo del chip.
3. **`map/`**: Funcionalidad opcional de geolocalización. Totalmente desacoplada; si esta capa falla, el `frontend/` sigue funcionando.
4. **`shared/`**: Utilidades compartidas y constantes específicas de este chip (por ejemplo, tipos de estado, plantillas).

## Dependencias Globales (`/core/`)

El Chip Reparto no es un componente aislado, sino que se integra en el ecosistema OmniWeb mediante el núcleo global:

- **Navegación (`/core/navigation/nav-system.js`)**: Gestiona la entrada al chip, el registro en el historial para volver al dashboard principal o la restauración de este chip al iniciar la aplicación.
- **Persistencia (`/core/state/state-manager.js`)**: Encargado del autoguardado de la sesión (ej. entregas confirmadas) y de cargar los datos de manera transparente al abrir la app o recargar la página. No se pierde progreso aunque se presione "Atrás".
