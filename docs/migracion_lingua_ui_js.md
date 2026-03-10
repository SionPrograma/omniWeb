# Informe de Migración: Archivos JS de la UI de Lingua

**Fecha:** 2026-03-10
**Módulo:** Lingua (UI)
**Estado:** Completado (Recuperación Funcional Mínima)

## 1. Archivos Encontrados y Verificados

Se han verificado y recuperado los siguientes archivos JavaScript requeridos por `ui/index.html`:

- `api.js`
- `ui.js`
- `app.js`

## 2. Origen -> Destino

| Archivo | Origen (Legacy) | Destino (OmniWeb) |
| :--- | :--- | :--- |
| `api.js` | `...\OmniWeb-VideoTranslator-MVP\frontend\js\api.js` | `01-omniweb\modules\lingua\ui\js\api.js` |
| `ui.js` | `...\OmniWeb-VideoTranslator-MVP\frontend\js\ui.js` | `01-omniweb\modules\lingua\ui\js\ui.js` |
| `app.js` | `...\OmniWeb-VideoTranslator-MVP\frontend\js\app.js` | `01-omniweb\modules\lingua\ui\js\app.js` |

*Nota: Los archivos ya estaban presentes en el destino, pero han sido refrescados desde la fuente original de VideoTranslator-MVP para garantizar integridad.*

## 3. Archivos Equivalentes y Ajustes

- **Archivos faltantes:** No se detectaron archivos faltantes de los referenciados en el HTML. Los nombres coinciden exactamente con los esperados.
- **Ajustes Realizados:** No se han realizado modificaciones en la lógica interna. Los paths de la API se mantienen apuntando a `http://localhost:8000`, que es el puerto por defecto esperado para el backend.

## 4. Referencias Pendientes o Rotas

- **Conectividad Backend:** Aunque los archivos JS están presentes, las funciones de "Fetch" fallarán hasta que el backend del módulo Lingua esté operativo y escuchando en `localhost:8000`.
- **Integración con OmniWeb Shell:** La UI de Lingua reside actualmente en su propio subdirectorio. En fases futuras, se deberá integrar con el sistema de carga dinámica de módulos de OmniWeb.

## 5. Próximos Pasos Recomendados

1. **Prueba de UI Estática:** Verificar que `index.html` carga correctamente los estilos y scripts (sin errores 404).
2. **Setup de Backend:** Proceder con la formalización del backend de Lingua para responder a las peticiones iniciadas por `api.js`.
3. **Refactorización de Rutas:** Cuando el backend esté listo, asegurar que las rutas en `api.js` coincidan con los nuevos endpoints de FastAPI en OmniWeb.
