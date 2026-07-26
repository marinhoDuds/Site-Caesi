import sqlite3
import re
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
sql_path = os.path.join(base_dir, "database.sql")
db_path = os.path.join(base_dir, "database.db")

with open(sql_path, "r") as f:
    sql = f.read()

# Replace MySQL ENUMs and collations with basic types for SQLite
sql = re.sub(r"ENUM\([^)]+\)", "VARCHAR(255)", sql, flags=re.IGNORECASE)
sql = re.sub(r"COLLATE ascii_bin", "", sql, flags=re.IGNORECASE)
sql = re.sub(r"AUTO_INCREMENT", "", sql, flags=re.IGNORECASE)

print(sql)

# Remove lines starting with --
sql_clean = "\n".join([line for line in sql.split('\n') if not line.strip().startswith('--')])

# Try executing statements one by one
with sqlite3.connect(db_path) as conn:
    conn.execute("PRAGMA foreign_keys = ON;")
    statements = sql_clean.split(';')
    for stmt in statements:
        if stmt.strip() and not stmt.strip().startswith('--'):
            print(f"Executing: {stmt.strip()}")
            try:
                conn.execute(stmt)
            except Exception as e:
                print(f"Failed: {e}")
