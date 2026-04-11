# PHASE 3 — OPEN SOURCE ORCHESTRATOR PATCH

Add a governed orchestration layer for open-source models/tools.

## Goal
Omni must be able to manipulate and combine open-source capabilities under its own authority.

## Required Components
- model registry
- provider adapter base contract
- capability router
- local vs remote preference handling
- evaluation hooks
- safety policy gate

## Supported Concept Types
- local llm
- embeddings
- code review engine
- summarizer
- diff explainer
- documentation helper

## Hard Rule
Omni decides; external models execute.
No external model should be treated as authority.
