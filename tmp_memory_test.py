import os
from backend.core.ai_host.memory.semantic_memory import SemanticMemoryBuffer
from backend.core.ai_host.intent_understanding.conversation_tracker import ConversationTracker

print('Testing Memory States')
# Add fake history to simulate previous state
semantic_memory = SemanticMemoryBuffer()
semantic_memory.add_interaction('Test mission: build a rocket', 'Okay.', 'BUILD_INTENT')

tracker1 = ConversationTracker()
tracker1.set_mission('default_user', 'build a rocket')

# Simulate a restart
print('Simulating restart...')
del semantic_memory
del tracker1

# Reload from disk
new_semantic_memory = SemanticMemoryBuffer() # auto loads from disk
new_tracker = ConversationTracker() # auto hydrates
# but we need to inject the newly created semantic_memory to prevent using the global empty one if any?
# Wait! It uses the global one! So let's override the global!

import backend.core.ai_host.memory.semantic_memory as sm
sm.semantic_memory = new_semantic_memory
new_tracker._hydrate_from_semantic_memory()

ctx = new_tracker.get_context('default_user')
print('Topic after restart:', ctx.last_topic)
print('Intent after restart:', ctx.last_intent)
print('Recent msgs:', ctx.recent_messages)
