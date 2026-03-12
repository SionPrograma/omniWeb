import logging
from typing import List, Dict, Optional
from .window_models import WebWindow, LayoutConfig

logger = logging.getLogger(__name__)

class WebWindowController:
    """Manages floating web windows and interface layout."""
    
    def __init__(self):
        self.windows: Dict[str, WebWindow] = {}
        self.config = LayoutConfig()

    def create_window(self, url: str, title: Optional[str] = None) -> WebWindow:
        if not title:
            title = url.split("//")[-1].split("/")[0]
            
        win = WebWindow(url=url, title=title)
        self.windows[win.id] = win
        logger.info(f"WebWindow: Created window for {url}")
        return win

    def close_window(self, window_id: str):
        if window_id in self.windows:
            del self.windows[window_id]

    def update_config(self, theme: str = None, brightness: float = None):
        if theme: self.config.theme = theme
        if brightness is not None: self.config.brightness = brightness

web_window_controller = WebWindowController()
