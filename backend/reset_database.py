import sqlite3
import os

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'database', 'parking.db')

# Delete old database if exists
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"🗑️ Deleted old database: {db_path}")

# Create fresh database with correct schema
print("Creating fresh database...")

# Import and run init_db from app.py
from app import init_db
init_db()

print("✅ Database reset complete!")
