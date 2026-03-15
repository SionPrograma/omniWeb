from .qr_token_manager import qr_token_manager

class QRValidationEngine:
    """
    Cryptographic and logical validation for QR tokens.
    Ensures that tokens are not only present but structurally valid and active.
    """
    
    def validate_incoming_scan(self, token_str: str) -> bool:
        """
        Structural and security check for tokens.
        """
        # 1. Length check
        if len(token_str) < 20: 
            return False
            
        # 2. Manager check
        token = qr_token_manager.validate_token(token_str)
        if not token:
            return False
            
        return True

qr_validation_engine = QRValidationEngine()
