# Dashboard Dinámico basado en Metadata (v1.0)

Este documento describe la evolución del Dashboard de OmniWeb de una estructura estática a una alimentada dinámicamente por el sistema.

## 1. Arquitectura de Datos

El Dashboard ya no hardcodea las tarjetas de los chips. En su lugar, utiliza el siguiente flujo:

1.  **Backend discovery**: `ModuleRegistry` escanea las carpetas en `chips/` y lee sus archivos `chip.json`.
2.  **Endpoint API**: Se ha habilitado la ruta `/api/v1/system/chips` en `backend/main.py` que expone la lista de módulos registrados con su metadata completa.
3.  **Frontend fetch**: Al cargar el Dashboard, un script Vanilla JS solicita la lista de chips mediante `fetch`.
4.  **Renderizado**: Se generan dinámicamente los elementos `<a>` (cards) aplicando estilos de "Glassmorphism" y animaciones aleatorias para mantener la estética espacial.

## 2. Lógica de Presentación

- **Visibilidad**: Solo se muestran los chips que tienen `dashboard_visible: true` en su metadata.
- **Estado Visual**:
  - **Active**: Chips con prefijo de backend o marcados como funcionales.
  - **Placeholder**: Se renderizan con estilo "Coming Soon" y sin enlace.
- **Resiliencia**: Si la API falla, el Dashboard simplemente no renderizará las cards, pero el resto de la UI (estrellas, cabecera) seguirá funcionando.

## 3. Persistencia de Sesión (Reciente)

El sistema de "Última Sesión" se ha integrado en el flujo dinámico. Una vez renderizados los chips, el script busca en `localStorage` el slug del último chip visitado y aplica un resaltado visual (borde esmeralda) y cambia el estado a "Reciente".

## 4. Beneficios
- **Cero duplicación**: Añadir un nuevo chip solo requiere crear su carpeta y metadata; el Dashboard lo detectará automáticamente.
- **Consistencia**: El nombre y descripción mostrados en la UI siempre coincidirán con la definición técnica del chip.
