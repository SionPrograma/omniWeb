import os
import re

migrations_dir = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb\backend\data\migrations"

for filename in os.listdir(migrations_dir):
    if filename.endswith(".sql"):
        filepath = os.path.join(migrations_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replace CREATE INDEX with CREATE INDEX IF NOT EXISTS
        # but avoid double IF NOT EXISTS
        new_content = re.sub(r"CREATE INDEX (?!IF NOT EXISTS)", "CREATE INDEX IF NOT EXISTS ", content)
        
        if new_content != content:
            print(f"Updating {filename}")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
