# PHASE 2 — CREATOR COMMAND GATEWAY PATCH

Create an additive command gateway so the Creator chatbot becomes the unified entrypoint for missions.

## Goal
When the Creator types a mission, the system should normalize it into a structured internal command object:
- raw_input
- intent
- execution_mode
- target_scope
- needs_tools
- needs_models
- needs_approval
- context_sources

## Requirements
- no UI rewrite
- no breaking current chat flow
- additive wrapper/adaptor only
- connect to existing ai host/brain/router where possible
- log normalized command for debug/runtime evidence

## Expected Result
Chat becomes the control surface without losing current shell/chat usability.
