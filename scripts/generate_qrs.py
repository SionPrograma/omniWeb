import sys
import os
import logging

# Ensure the root of the project is in the Python path
sys.path.append(os.getcwd())

from backend.core.qr_gateway.qr_token_manager import qr_token_manager
from backend.core.qr_gateway.qr_visual_generator import qr_visual_generator

logging.basicConfig(level=logging.INFO)

def main():
    print("Starting QR generation...")
    # Ensure output directory exists (using forward slashes for cross-platform safety)
    os.makedirs('deployment/qr_access', exist_ok=True)
    os.makedirs('Desktop/QRs', exist_ok=True)

    roles = ['creator', 'admin', 'admin_candidate', 'beta_tester', 'public']
    for role in roles:
        print(f"Generating token for {role}...")
        token = qr_token_manager.generate_token(role, expires_in=31536000, single_use=False)
        # Use a realistic local URL for now
        join_url = f'http://localhost:8000/api/v1/qr/join?token={token}'
        
        print(f"Creating QR image for {role}...")
        path = qr_visual_generator.generate_branded_qr(f'omniweb_qr_{role}', join_url)
        print(f"Generated QR (PNG): {path}")
        
        svg_path = qr_visual_generator.generate_svg(f'omniweb_qr_{role}', join_url)
        print(f"Generated QR (SVG): {svg_path}")

    print("QR generation completed successfully.")

if __name__ == "__main__":
    main()
