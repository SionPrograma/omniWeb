# PHASE 5 — FILE SCOPE GUARD + CHECKPOINT MANAGER

Add file governance before real mutation.

## Must include
- scope isolation
- logical lock by file/module
- patch proposal state
- checkpoint creation
- rollback metadata
- approval gate before apply

## Intent
Allow multiple subagents/models to collaborate without corrupting runtime or files.
