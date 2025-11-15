import sqlite3
import sys
sys.path.insert(0, '.')
from app import init_db

# Initialize database
init_db()

# Check schema
conn = sqlite3.connect('database/parking.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
print("Users table columns:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")
conn.close()
