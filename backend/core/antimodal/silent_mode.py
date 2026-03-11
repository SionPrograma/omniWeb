import logging

logger = logging.getLogger(__name__)

class SilentModeHandler:
    """
    Handles behavior when the system is in silent / background operation.
    Requirement: no rich UI unless explicitly requested.
    Requirement: security-relevant messages must still appear.
    Requirement: in silent mode, visual panels should not open automatically.
    """
    def __init__(self):
        pass

    def should_suppress_ui(self, message_type: str) -> bool:
        """
        Determine if UI feedback should be suppressed.
        Critical security alerts (auth, permissions) must never be suppressed.
        """
        critical_types = ["security", "auth_failure", "permission_error", "critical_system_error"]
        
        if message_type in critical_types:
            logger.info(f"Critical message {message_type} bypasses silent suppression.")
            return False
            
        return True

    def filter_ui_elements(self, elements: list) -> list:
        """
        Filter visual panels that should not open automatically in silent mode.
        """
        # List of intrusive UI components that should be avoided
        intrusive = ["full-panel", "hero-section", "modal-rich-voice", "overlay"]
        
        # If in silent mode, filter these out unless they have 'urgent' or 'safety' tag
        filtered = []
        for el in elements:
            if el.get("type") in intrusive and not el.get("urgent", False):
                logger.debug(f"Suppressed panel {el.get('type')} in silent mode.")
                continue
            filtered.append(el)
            
        return filtered

silent_handler = SilentModeHandler()
