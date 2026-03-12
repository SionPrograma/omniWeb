import logging
import html

logger = logging.getLogger(__name__)

class IFrameRenderer:
    """Generates secure and styled IFrame containers for web windows."""
    
    def render(self, url: str, title: str) -> str:
        """Returns the HTML string for the window content."""
        safe_url = html.escape(url)
        safe_title = html.escape(title)
        return (
            f'<iframe src="{safe_url}" title="{safe_title}" '
            'sandbox="allow-scripts allow-same-origin allow-forms" '
            'loading="lazy"></iframe>'
        )

iframe_renderer = IFrameRenderer()
