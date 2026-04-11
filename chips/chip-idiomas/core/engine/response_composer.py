from typing import Optional
from .policy_layer import LanguagePolicyLayer
from .tool_adapter import LanguageToolAdapterLayer
from .safe_fallback import SafeFallbackLayer

class ResponseComposer:
    def __init__(self):
        self.policy = LanguagePolicyLayer()
        self.tool_adapter = LanguageToolAdapterLayer()
        self.fallback = SafeFallbackLayer()
        
    def compose(self, intent_info: dict, chat_context: dict = None) -> Optional[str]:
        # 1. Try to use advanced model/tools via ToolAdapter if active
        response = None
        
        intent_type = intent_info.get("type")
        
        if intent_type == "translation":
            # Attempt real translation if Stage C enabled
            response = self.tool_adapter.generate_translation(intent_info.get("extracted_text", ""))
            
        if not response and self.tool_adapter.llama_active:
             # Attempt semantic completion
             response = self.tool_adapter.generate_semantic_completion(intent_info)
             
        # 2. If tools are inactive or failed, use Safe Fallback
        if not response:
            response = self.fallback.generate(intent_info)
            
        # 3. If intent was unknown, return None to safely drop out of chip-idiomas
        # so GeneralChatProcessor can handle it unhindered.
        if not response:
            return None
            
        # 4. Enforce Policy (Tone, Guidelines)
        final_response = self.policy.evaluate(response, intent_info)
        
        return final_response
