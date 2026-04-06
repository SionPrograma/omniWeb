import sqlite3

def list_tables_and_columns(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table_name in tables:
        table_name = table_name[0]
        print(f"\nTable: {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name});")
        info = cursor.fetchall()
        for i in info:
            print(i)
    conn.close()

if __name__ == "__main__":
    list_tables_and_columns("backend/omni.db")
