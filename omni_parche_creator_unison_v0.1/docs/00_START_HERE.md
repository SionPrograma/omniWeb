# START HERE

## Objetivo del parche
Conseguir que **todo el gobierno operativo pase por Creator Mode**, usando el chatbot como superficie principal.
Desde ahí Omni debe poder:
- recibir una misión por chat/voz
- entender intención y contexto
- orquestar herramientas y modelos open source
- auditarse
- compararse con outputs/código open source
- proponer mejoras
- ejecutar cambios de forma aditiva y controlada
- pedir confirmación para aplicar cambios sensibles/finales

## Resultado esperado
Un estado de **unísono operativo** entre:
- chatbot del Creator Mode
- workspace/editor
- chips
- dashboard
- auditoría
- herramientas open source
- evaluación y mejora de herramientas propias

## Principios duros
- additive only
- no destructive refactor
- no romper flujos existentes
- 1 misión = 1 capa
- runtime truth mandatory
- human approval required for sensitive actions
- Omni must govern external tools/models, not depend on them as authority

## Núcleo del parche
1. Command Gateway desde Creator chat
2. Capability Router
3. Open Source Model Registry
4. Provider Adapter Layer
5. Workspace Bridge
6. File Scope Guard
7. Checkpoint Manager
8. Response Critic / Audit Layer
9. Evaluation Ledger
10. Creator-facing orchestration surface
