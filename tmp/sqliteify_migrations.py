import os
import re

migrations_dir = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb\backend\data\migrations"

patterns = [
    (r"CREATE TYPE \w+ AS ENUM \([^)]+\);", ""), # Remove Enum types
    (r"TIMESTAMP WITH TIME ZONE", "DATETIME"),
    (r"JSONB", "TEXT"),
    (r"UUID", "TEXT"),
    (r"task_status", "TEXT"), # Specific to 022
    (r"ON CONFLICT \(node_id\) DO NOTHING", ";"), # SQLite uses INSERT OR IGNORE or similar, but let's just make it simple if it's an INSERT
]

# Actually, SQLite supports ON CONFLICT (name) DO NOTHING in recent versions, 
# but let's check if it's supported by the system sqlite.

for filename in os.listdir(migrations_dir):
    if filename.endswith(".sql"):
        filepath = os.path.join(migrations_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        new_content = content
        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, new_content, flags=re.IGNORECASE)
        
        # Specific fix for ON CONFLICT in SQLite
        # SQLite: INSERT INTO ... ON CONFLICT(id) DO NOTHING;
        # Wait, the PG syntax is very similar.
        
        if new_content != content:
            print(f"Updating {filename} for SQLite compatibility")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
