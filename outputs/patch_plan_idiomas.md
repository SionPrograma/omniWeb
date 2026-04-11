# PATCH PLAN: chip-idiomas Integration

## Architectural Objective
Introduce `chip-idiomas` as a dedicated processor intercepting the end-stage response composing and general multilingual chatting, while preserving Sovereign OmniWeb authority for active technical missions.

## Strategy: Additive Minimum Viable Patch
Currently, if Omniverse falls into `_handle_natural_chat` in `brain_router.py`, it defers blindly to `GeneralChatProcessor`. We will intercept this. 

## Files to Modify:
1. `backend/core/ai_host/brain_router.py`
   - **Change:** Inject `chip-idiomas` check in `_handle_natural_chat`. If the chip is active and installed, route contextual chatter to it first. If it yields an enhanced response, use it. Otherwise, fallback safely to `GeneralChatProcessor`.
   - **Why:** Non-destructive. Maintains fast-path fallback and isolates language understanding away from routing logic.

## Files to Create:
1. `chips/chip-idiomas/chip.json`: Registers the module.
2. `chips/chip-idiomas/core/__init__.py`: Package init.
3. `chips/chip-idiomas/core/router.py`: Minimal default backend mount point.
4. `chips/chip-idiomas/core/services/language_engine.py`: 
   - **Logic:** The module exposing `enhance_natural_chat`. Contains future scaffolding for Qwen / llama.cpp / multilingual embedding support. For this mission, it provides a functional local validation response.

## Validation Method:
Check `/status` or `/process` in the host, ensuring the launcher functions, the chip registers correctly without regressions.
