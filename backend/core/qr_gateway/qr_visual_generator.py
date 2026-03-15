import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class QRVisualGenerator:
    """
    Generates branded, technological-looking QR codes for OmniWeb.
    """
    
    def __init__(self, base_path: str = "deployment/qr_access"):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def generate_branded_qr(self, name: str, data: str, logo_path: Optional[str] = None):
        """
        Creates a high-contrast, technological-themed QR code.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Apply OmniWeb styling: Cyan radial gradient on dark background
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            color_mask=RadialGradiantColorMask(
                back_color=(5, 5, 8),      # OmniWeb Dark Deep Blue
                center_color=(0, 212, 255), # OmniWeb Cyan
                edge_color=(0, 60, 100)     # Dark transition
            )
        )

        output_path = os.path.join(self.base_path, f"{name}.png")
        img.save(output_path)
        logger.info(f"QR Generated: {output_path}")
        return output_path

    def generate_svg(self, name: str, data: str):
        """
        Generates an SVG version of the QR code.
        """
        import qrcode.image.svg
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
            image_factory=qrcode.image.svg.SvgPathImage
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image()
        
        output_path = os.path.join(self.base_path, f"{name}.svg")
        img.save(output_path)
        logger.info(f"SVG QR Generated: {output_path}")
        return output_path

qr_visual_generator = QRVisualGenerator()
