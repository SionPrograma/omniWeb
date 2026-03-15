import os
import re

migrations_dir = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb\backend\data\migrations"

patterns = [
    (r"ALTER TABLE (\w+) ADD COLUMN IF NOT EXISTS (\w+) ([^;]+);", r"ALTER TABLE \1 ADD COLUMN \2 \3;"),
]

for filename in os.listdir(migrations_dir):
    if filename.endswith(".sql"):
        filepath = os.path.join(migrations_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        new_content = content
        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, new_content, flags=re.IGNORECASE)
        
        if new_content != content:
            print(f"Updating {filename} for ALTER TABLE compatibility")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
