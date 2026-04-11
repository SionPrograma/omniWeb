# PHASE 4 — WORKSPACE BRIDGE PATCH

Connect Creator chat to workspace/editor and internal tools through a governed bridge.

## Target Actions
- inspect active file
- request diff
- request explanation
- request compare
- propose patch
- open chip
- inspect dashboard surface
- collect runtime evidence

## Constraints
- additive only
- do not bypass existing permission layers
- prefer reuse of current editor / diff preview / builder flow if present
- all actions must return structured evidence to Creator chat
