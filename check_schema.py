
import sqlite3

conn = sqlite3.connect('backend/omni.db')
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(system_missions)")
cols = cursor.fetchall()

for col in cols:
    print(col)

conn.close()
