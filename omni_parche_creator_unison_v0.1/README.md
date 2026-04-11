# OMNI PARCHE — Creator Unison Patch v0.1

Este paquete está pensado como **parche aditivo y no destructivo** para OmniWeb.
Su propósito es ayudar a integrar una capa donde el **chatbot del Creator Mode**
pueda orquestar herramientas, workspace, chips, dashboard, auditoría, comparación
con código/modelos open source y mejora progresiva de herramientas propias.

## Qué contiene
- `docs/` explicación estratégica del parche
- `prompts/` prompts ordenados para ejecutar con Antigravity
- `scaffolds/` archivos `.py` de referencia para parche aditivo

## Regla principal
**Omni gobierna.**
Los modelos open source, herramientas y agentes actúan como capacidades subordinadas.

## Importante
Los `.py` incluidos aquí son **scaffolds aditivos** y no asumen exactitud absoluta de rutas
sobre tu repo real. Están pensados como base para que Antigravity:
1. audite la estructura actual
2. ubique el módulo equivalente
3. aplique cada parche sin romper el sistema existente

## Orden recomendado
1. Leer `docs/00_START_HERE.md`
2. Ejecutar prompts en orden numérico
3. Crear/ajustar módulos scaffold donde corresponda
4. Verificar runtime después de cada misión
5. Crear checkpoint/commit estable tras cada fase válida
