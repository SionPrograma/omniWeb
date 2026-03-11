# Normalización de Responsabilidades (OmniWeb v0.2.0)
ADR: Aclaración Estructural Fase 1

## Resumen del Patrón Arquitectónico
OmniWeb v0.2.0 opera bajo un modelo **MPA (Multi-Page Application) dinámico**.
No es una SPA (Single Page Application). La navegación principal depende de recargas tradicionales de rutas orquestadas por **FastAPI**, donde cada ruta devuelve un documento HTML contenido y aislado que inicializa su propio ecosistema de módulos JavaScript (Vanilla JS).

## Ambigüedades Estructurales Detectadas
El crecimiento orgánico del repositorio generó nombres superpuestos o convenciones congnitivamente ambiguas:
1. `core/` vs `backend/core/` (Superposición de dominio "Platform Core").
2. `frontend/` vs `chips/[chip]/frontend/` (Ambigüedad sobre dónde escribir UI).
3. `main.py` vs API Routers (Dónde vive la orquestación vs lógica de negocio).

## Decisiones y Convenciones Oficiales v0.2.0

### 1. La División del Core
Para evitar refactors masivos que rompan los miles de imports relativos (`import '/core/...'`), se establece:
- **`core/` (Raíz)**: Es única y exclusivamente el **Core del Cliente (Frontend Vanilla JS)**. Administra navegación (`nav-system`), estado local persistente (`state-manager`) y utilidades visuales compartidas en el navegador (OmniShell). Todo su código se ejecuta cruzando la red, en el cliente web.
- **`backend/core/`**: Es el **Núcleo del Servidor (Server Hub en Python)**. Controla el montaje general de FastApi, las lecturas de entorno (`config.py`) y el motor de descubrimiento de módulos al arrancar. Jamás maneja renderizado o DOM.

### 2. El Alcance del Frontend
- **`frontend/dashboard/`**: En OmniWeb v0.2.0, la carpeta raíz `frontend/` **NO** representa la carpeta global de la aplicación web como sucedería en Vite/React. Solo es responsable de renderizar el "Centro de Mando" (Hub/Portal) que se levanta bajo la ruta base de la API (`/`).
- **`chips/`**: Cada dominio funcional (reparto, finanzas, idiomas) que tiene su propia carpeta es un "Chip". Los desarrollos, maquetas y scripts de pantallas individuales viven dentro de `chips/{nombre_del_chip}/frontend/`.

### 3. El Rol de fastapi
- **`backend/main.py`**: Intercepta de forma estática las carpetas de los chips y levanta automáticamente sus recursos sin recargar el `main.py`. Este archivo no debe conocer lógica de negocio, es solo un "orquestador ciego" guiado por una lista (`ACTIVE_MODULES` en `backend/core/config.py`).

## Conclusión
Se evita cambiar de stack (SPA) priorizando el estado MPA por su pureza, resistencia, y facilidad de encapsulamiento. Si se requiere añadir una pantalla nueva, jamás se tocará `core/` ni el `frontend/dashboard/` (salvo para enlazarla), sino que se desarrollará en aislamiento total dentro de `chips/*/frontend`.
