# AUDIT: OmniWeb Chatbot & Lingua Pipeline

## 1. Current Chatbot Architecture Map
- **Entrypoint:** `backend/core/ai_host/routing/router.py` (`/process`)
- **Intent Parser:** `backend/core/ai_host/intent_understanding/human_input_interpreter.py`
- **Orchestration / Routing:** `backend/core/ai_host/routing/command_router.py`
  - Highly overloaded. Contains large hardcoded intent dictionaries (`_FAST_GREETINGS`, `_FAST_IDENTITY`) which bypass NLP to gain speed.
- **Cognitive / Deliberation Engine:** `backend/core/ai_host/brain_router.py`
  - Routes complex logic vs. conversational fallback (`_handle_natural_chat`). 
- **Synthesis Engine:** `backend/core/ai_host/orchestration/executive_synthesis.py`
  - Handles text generation by filling templates with context. Has an embedded "honest feedback" mechanism that triggers rigid responses (e.g., "Me perdí un poco").

## 2. Current Lingua Status
- `chip-lingua`: Exists in `chips/chip-lingua/`. Operates as a utility backend for async AV transcriptions, translations, and TTS generation (Media pipeline).
- `chip-idiomas-ia`: Exists in `chips/chip-idiomas-ia/`. pure frontend tool, inactive architecture.
- Both fail to hook into the Chatbot pipeline, meaning conversational language logic is trapped natively in `GeneralChatProcessor` and `executive_synthesis`.

## 3. Broken / Weak Points
**Why the Chatbot feels Uncoordinated:**
1. **Hardcoded Overrides:** Natural conversation relies on exact string checking instead of NLP semantic mapping (e.g., if a user asks a complex technical question that begins with "hola", the rigid parser might swallow it).
2. **Context Bleed:** The system merges strict logic operations ("Audita X") with linguistic handling ("Explícamelo en francés").
3. **Synthesis Looping:** When intent drops below thresholds, `executive_synthesis` provides robotic defaults, preventing dynamic re-routing.
4. **Poor formatting:** Fallbacks do not rewrite responses into well-structured paragraphs, but simply concat logic strings.

## 4. Reusable Pieces to Preserve
- `brain_router.py` flow: `_process_analysis` for tasks vs `_handle_natural_chat`.
- The Module Registry: Autodiscovery handles chip registration beautifully.

## 5. Risk Zones
- Do NOT rewrite `command_router.py` rule chains or `_is_local_fast_path` directly to avoid breaking Creator mode latency. Additive interception is required.
