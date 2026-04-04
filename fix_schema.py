
import sqlite3

conn = sqlite3.connect('backend/omni.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE system_missions ADD COLUMN visual_context TEXT")
    cursor.execute("ALTER TABLE system_missions ADD COLUMN multimodal_history TEXT")
    print("Columns added successfully")
except Exception as e:
    print(f"Error adding columns: {e}")

conn.commit()
conn.close()
