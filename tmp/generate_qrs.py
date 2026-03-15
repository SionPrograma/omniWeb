import qrcode
import os

qr_dir = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb\deployment\qr_access"
os.makedirs(qr_dir, exist_ok=True)

# URL Pattern
base_url = "https://omniweb.app/shell?invite="

qrs = [
    ("omniweb_qr_beta_tester.png", "OMNI-BETA-ACCESS"),
    ("omniweb_qr_admin_candidate.png", "OMNI-CANDIDATE-PROMOTION"),
    ("omniweb_qr_administrator.png", "OMNI-ADMIN-COMMAND")
]

for filename, token in qrs:
    url = base_url + token
    print(f"Generating QR for {token} -> {filename}")
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(os.path.join(qr_dir, filename))

print("QR codes generated in deployment/qr_access/")
