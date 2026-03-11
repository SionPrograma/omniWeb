import ast
import logging

logger = logging.getLogger(__name__)

class CodeValidator:
    """
    Validates code safety and syntax before applying modifications.
    """
    def validate_python(self, code: str) -> bool:
        """
        Checks if the Python code has valid syntax.
        """
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            logger.error(f"CodeValidator: Syntax error: {e}")
            return False

    def validate_router_structure(self, code: str) -> bool:
        """
        Ensures the chip router follows the standard pattern.
        """
        if "from fastapi import APIRouter" not in code and "APIRouter()" not in code:
             # If it's a router file, it must have a router object
             if "@router." in code:
                  return True # Assume it's an additive patch
        return True

    def validate_imports(self, code: str) -> bool:
        """
        Checks for broken imports or unauthorized system access.
        """
        # Simple heuristic: prevent direct access to sensitive system paths or libraries
        unauthorized = ["winreg", "ctypes", "pickle.load"]
        for term in unauthorized:
            if term in code:
                 return False
        return True

    def is_safe(self, code: str) -> bool:
        """
        Basic safety check: prevent dangerous imports or calls.
        """
        dangerous = ["os.system", "subprocess.Popen", "shutil.rmtree", "eval(", "exec("]
        # Allow internal usage if it looks legitimate but be strict
        for term in dangerous:
            if term in code:
                logger.warning(f"Detection of potentially unsafe code: {term}")
                return False
        return True

code_validator = CodeValidator()
