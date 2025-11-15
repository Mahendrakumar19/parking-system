"""
Quick Setup - Create predefined users
Run this AFTER starting the server at least once (python app.py)
"""
import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Connect to database (check both possible locations)
import os
if os.path.exists('backend/database/parking.db'):
    db_path = 'backend/database/parking.db'
elif os.path.exists('database/parking.db'):
    db_path = 'database/parking.db'
else:
    print("❌ Database not found! Please start the server first: python app.py")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Predefined users
users = [
    ('U001', 'Admin User', '9999999999', 'Admin Office, University Campus', 'Administration', 'ADMIN001', 'admin@parking.com', 'admin123'),
    ('U002', 'John Doe', '9876543210', '123 Main Street, City', 'Computer Science', 'STU001', 'john@gmail.com', 'john123'),
    ('U003', 'Jane Smith', '9876543211', '456 Park Avenue, City', 'Electrical Engineering', 'STU002', 'jane@gmail.com', 'jane123'),
    ('U004', 'Test User', '9876543212', '789 College Road, City', 'Mechanical Engineering', 'STU003', 'test@gmail.com', 'test123'),
    ('U005', 'Rajesh Kumar', '9876543213', '321 University Lane, City', 'Civil Engineering', 'STU004', 'rajesh@gmail.com', 'rajesh123'),
]

print("🔐 Creating predefined users...\n")

for user_id, name, mobile, address, dept, univ_id, email, password in users:
    try:
        cursor.execute('''
            INSERT INTO users (user_id, name, mobile, address, department, university_id, email, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, mobile, address, dept, univ_id, email, hash_password(password)))
        
        role = "👑 ADMIN" if email == 'admin@parking.com' else "👤 USER"
        print(f"✅ {name} ({email}) - {role}")
        print(f"   Password: {password}")
    except sqlite3.IntegrityError:
        print(f"⚠️  Skipped: {email} (already exists)")

conn.commit()
conn.close()

print("\n" + "="*60)
print("🔐 LOGIN CREDENTIALS")
print("="*60)
print("\n👑 ADMIN (Scanner + All Bookings):")
print("   Email: admin@parking.com | Password: admin123")
print("\n👤 USERS:")
print("   Email: john@gmail.com    | Password: john123")
print("   Email: jane@gmail.com    | Password: jane123")
print("   Email: test@gmail.com    | Password: test123")
print("   Email: rajesh@gmail.com  | Password: rajesh123")
print("\n✅ Start server: python app.py")
print("📱 Login at: http://localhost:5000")
