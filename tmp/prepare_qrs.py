import qrcode
import os
import shutil

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
qr_source = os.path.join(base_dir, "deployment", "qr_access")
desktop_qr = os.path.join(os.path.expanduser("~"), "Desktop", "QRs")

# Generate Creator and Public QR codes if they don't exist
creator_path = os.path.join(qr_source, "omniweb_qr_creator.png")
public_path = os.path.join(qr_source, "omniweb_qr_public.png")

if not os.path.exists(creator_path):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data("OMNI-CREATOR-CONTROL")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(creator_path)
    print(f"Created: {creator_path}")
else:
    print(f"Already exists: {creator_path}")

if not os.path.exists(public_path):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data("OMNI-PUBLIC-ACCESS")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(public_path)
    print(f"Created: {public_path}")
else:
    print(f"Already exists: {public_path}")

# Copy to Desktop/QRs
os.makedirs(desktop_qr, exist_ok=True)

qr_files = [
    "omniweb_qr_creator.png",
    "omniweb_qr_public.png",
    "omniweb_qr_beta_tester.png",
    "omniweb_qr_admin_candidate.png",
    "omniweb_qr_administrator.png",
]

for f in qr_files:
    src = os.path.join(qr_source, f)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(desktop_qr, f))
        print(f"Copied to Desktop/QRs: {f}")
    else:
        print(f"Warning: {f} not found in source")

print(f"\nDesktop QR folder ready: {desktop_qr}")
print("Done!")
