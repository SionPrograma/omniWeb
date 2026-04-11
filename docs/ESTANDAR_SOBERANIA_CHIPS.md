# Estándar de Soberanía y Naturalización de Chips (v1.1)

Este documento define el estándar oficial para la integración de módulos (chips) en el ecosistema OmniWeb. La adherencia a este estándar garantiza la estabilidad del arranque, el cumplimiento de la seguridad perimetral y la independencia funcional de los módulos.

## 1. Reglas de Oro de la Soberanía

### A. Neutralidad en Tiempo de Importación (Import-Time Neutrality)
**PROHIBICIÓN ESTRICTA**: Ningún archivo de un chip debe ejecutar efectos secundarios durante su importación.
*   **No** iniciar conexiones a bases de datos.
*   **No** crear sockets de red.
*   **No** instanciar clases cuyo constructor (`__init__`) acceda a recursos externos del sistema.
*   **Razón**: El sistema opera un handshake de seguridad durante el arranque que se bloquea si el chip intenta acceder a recursos antes de que su identidad sea verificada en el registro.

### B. Activación Diferida (Deferred Activation)
Toda lógica de persistencia o inicialización de recursos debe ser **perezosa (Lazy)**.
*   El patrón obligatorio es `_ensure_initialized()` o `_ensure_db()`.
*   La inicialización debe ocurrir únicamente durante la primera operación real (ej: la primera petición HTTP al router del chip).

### C. Lealtad a la Metadata (Metadata Integrity)
*   El chip solo puede utilizar capacidades declaradas explícitamente en su `chip.json` bajo la clave `permissions`.
*   El Core denegará por defecto cualquier intento de acceso a recursos (DB, Storage, etc.) no autorizados en la metadata.

---

## 2. Estados Oficiales del Chip (Registry Status)

| Estado | Significado | Comportamiento |
| :--- | :--- | :--- |
| **`ok`** | Naturalización Exitosa | Chip híbrido con backend y frontend activos. |
| **`booting`** | Pre-registro Transitorio | Estado temporal para resolver identidades durante el arranque. |
| **`damaged_backend`** | Fallo de Descubrimiento | Error en importación o montaje. El chip cae a modo seguro (Frontend-only). |
| **`frontend_only`** | Módulo Ligero | Chip sin backend por diseño. |
| **`missing_router`** | Conflicto de Metadata | El chip declara backend pero el sistema no encuentra el router. |
| **`legacy_frozen`** | Módulo Conservado | Chip legado conservado por compatibilidad histórica; no expansible sin auditoría. |

---

## 3. Guía de Auditoría de Aceptación

Para que un chip sea aceptado en el ecosistema, debe superar este checklist:
1. [ ] **¿Cero Side-Effects?**: Correr `import chips.chip-nombre.core.router` y verificar que no genera logs de DB o seguridad.
2. [ ] **¿Lazy Init?**: Verificar que el repository usa el patrón `_ensure_db`.
3. [ ] **¿Soberanía de Datos?**: Verificar que accede solo a sus propias tablas de SQLite o APIs autorizadas.
4. [ ] **¿Degradación Identificada?**: Verificar que el sistema puede arrancar incluso si borramos la base de datos del chip.

---

## 4. Fallback de Seguridad
Si el sistema detecta que un chip viola el Estándar de Neutralidad durante el arranque, el `ModuleRegistry` lo marcará automáticamente como `damaged_backend`, aislando su lógica de servidor pero permitiendo que su interfaz (Frontend) siga siendo accesible como una PWA plana si es posible.
