# Sprint de Pulido: OmniWeb v0.2.1 (Stable)

## Objetivo
Preparar la versión v0.2.1 como un *checkpoint* de estabilidad. Nos enfocamos en consolidar la documentación técnica, asegurar las convenciones y confirmar que la arquitectura implementada en la v0.2.0 (Backend Centralizado + "Chips" en MPA + Portable First) es funcional, escalable y está lista para empaquetarse.

## Diagnóstico y Fricciones Detectadas (v0.2.0 -> v0.2.1)
1. **Falta de un Quick Start:** El `README.md` explicaba filosofía y arquitectura profundamente pero omitía los comandos básicos para que un tercero o nosotros mismos arranquemos localmente la solución.
2. **Versionado Inconsistente:** Archivos core como `config.py` o referencias textuales en el `README.md` apuntaban de forma hardcodeada a `v0.2.0`. Faltaba indicación visual de versión global en el frontend central (Dashboard).
3. **Persistencia / Falsas Expectativas**: No quedaba suficientemente claro para alguien externo que las BBDDs no existen todavía y que el sistema descansa íntegramente de manera transicional en "StateManagers" locales y variables en memoria de FastAPI, lo que podría generar falsas sensaciones de pérdida de datos si se reinicia agresivamente el servidor o el navegador. Necesita ser advertido como un *Feature Transicional* bajo el concepto de "Portable First".

## Resoluciones y Aplicaciones Pequeñas
A fin de resolver lo anterior sin alterar bajo ninguna circunstancia el paradigma de código, se aplicó:

- **Documentación Central Update:** Se modificó `README.md` agregando una sección clara de `🚀 Quick Start` que lista tres pasos para levantar Uvicorn. Se hizo énfasis literario en la estrategia "Portable First".
- **Naming Config Validation:** Se validó `backend/core/config.py` actualizando su flag `VERSION` a `0.2.1`.
- **Ajuste Menor UI (Shell):** Se introdujo una etiqueta de texto nativa pequeña en `frontend/dashboard/index.html` explícitamente debajo del título que dice `v0.2.1-stable`, inyectando seguridad técnica sobre qué entorno se navega.
- **Validación del Shell/Routing:** El enrutamiento actual basado en strings ("idiomas-ia", "reparto", "finanzas", "programacion") que el módulo de FastAPI escanea dinámicamente (`ACTIVE_MODULES`) funciona según lo diseñado y se consideró **ESTABLE**. 

## Estable y Transicional de Cara al Futuro

### ESTABLE (Qué quedó grabado en piedra para v0.2.1)
- La inyección estática de directorios vía `FastAPI.mount()`. El framework Python siempre será el despachador central.
- El modelo MPA Vanilla JS: no hay Webpack, no hay compilación. Cada vista se carga limpia y en crudo, siendo el navegador quien rutea localmente.
- Componente `nav-system` de `core/` funcionando como intercomunicador del *Back*.

### TRANSICIONAL (Documentar ahora, ejecutar después)
1. **La base de datos en memoria o local:** Todos los chips (Reparto, Finanzas) actualmente son transicionales respecto de donde conservan finalmente la información. A futuro un servicio global de Pydantic+SQLite debe absorberlos.
2. **Legado de Lingua (`modules/lingua/`)**: Queda en carpeta legacy. Es transicional hasta que su peso funcional se absorba en la ruta `/api/v1/idiomas-ia/` definitivamente. No se borra preventivamente para asegurar retrocompatibilidad funcional.

**OmniWeb v0.2.1** finaliza su sprint de solidificación y se considera listo para continuar explorando nuevos chips funcionales.
