
import logging

logger = logging.getLogger(__name__)

class OmniExpCore:
    def __init__(self):
        self.name = "OmniExp"
        
    def run(self):
        logger.info(f"Initializing {self.name} core logic.")
        return True

if __name__ == "__main__":
    core = OmniExpCore()
    core.run()
