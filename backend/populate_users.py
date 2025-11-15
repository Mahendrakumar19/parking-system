"""
Populate Database with Predefined Users
Creates admin and test user accounts

IMPORTANT: Run the Flask server (python app.py) at least once before running this script!
The server creates the database tables on first run.
"""
import sqlite3
import hashlib
import os
import sys

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'database', 'parking.db')

# Check if database exists
if not os.path.exists(db_path):
    print("❌ Error: Database not found!")
    print("💡 Please run the Flask server first: python app.py")
    print("   The server will create the database on first run.")
    print("   Then stop the server (Ctrl+C) and run this script again.")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if users table exists
try:
    cursor.execute("SELECT COUNT(*) FROM users")
    existing_users = cursor.fetchone()[0]
    
    if existing_users > 0:
        print(f"⚠️  {existing_users} user(s) already exist in database!")
        response = input("Do you want to add more users anyway? (y/n): ")
        if response.lower() != 'y':
            print("❌ Cancelled. No users added.")
            conn.close()
            sys.exit(0)
except sqlite3.OperationalError as e:
    print(f"❌ Error: Users table does not exist! ({e})")
    print("💡 Please run the Flask server first: python app.py")
    print("   The server will create the database tables on first run.")
    print("   Then stop the server (Ctrl+C) and run this script again.")
    conn.close()
    sys.exit(1)

print("\n🔐 Creating predefined user accounts...\n")

# Predefined users
users = [
    {
        'user_id': 'U001',
        'name': 'Admin User',
        'mobile': '9999999999',
        'address': 'Admin Office, University Campus',
        'department': 'Administration',
        'university_id': 'ADMIN001',
        'email': 'admin@parking.com',
        'password': 'admin123'
    },
    {
        'user_id': 'U002',
        'name': 'John Doe',
        'mobile': '9876543210',
        'address': '123 Main Street, City',
        'department': 'Computer Science',
        'university_id': 'STU001',
        'email': 'john@gmail.com',
        'password': 'john123'
    },
    {
        'user_id': 'U003',
        'name': 'Jane Smith',
        'mobile': '9876543211',
        'address': '456 Park Avenue, City',
        'department': 'Electrical Engineering',
        'university_id': 'STU002',
        'email': 'jane@gmail.com',
        'password': 'jane123'
    },
    {
        'user_id': 'U004',
        'name': 'Test User',
        'mobile': '9876543212',
        'address': '789 College Road, City',
        'department': 'Mechanical Engineering',
        'university_id': 'STU003',
        'email': 'test@gmail.com',
        'password': 'test123'
    },
    {
        'user_id': 'U005',
        'name': 'Rajesh Kumar',
        'mobile': '9876543213',
        'address': '321 University Lane, City',
        'department': 'Civil Engineering',
        'university_id': 'STU004',
        'email': 'rajesh@gmail.com',
        'password': 'rajesh123'
    }
]

added_count = 0
skipped_count = 0

for user in users:
    try:
        # Check if user already exists
        cursor.execute("SELECT email FROM users WHERE email = ?", (user['email'],))
        if cursor.fetchone():
            print(f"⚠️  Skipped: {user['email']} (already exists)")
            skipped_count += 1
            continue
        
        # Insert user
        cursor.execute('''
            INSERT INTO users (user_id, name, mobile, address, department, university_id, email, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user['user_id'],
            user['name'],
            user['mobile'],
            user['address'],
            user['department'],
            user['university_id'],
            user['email'],
            hash_password(user['password'])
        ))
        
        # Determine role
        role = "👑 ADMIN" if user['email'] == 'admin@parking.com' else "👤 USER"
        print(f"✅ Created: {user['name']} ({user['email']}) - {role}")
        print(f"   User ID: {user['user_id']} | Password: {user['password']}")
        added_count += 1
        
    except Exception as e:
        print(f"❌ Error creating {user['email']}: {e}")

conn.commit()
conn.close()

print("\n" + "="*60)
print("📊 SUMMARY")
print("="*60)
print(f"✅ Users created: {added_count}")
print(f"⚠️  Users skipped: {skipped_count}")

if added_count > 0:
    print("\n🔐 LOGIN CREDENTIALS:")
    print("="*60)
    print("\n👑 ADMIN ACCOUNT (Full Access):")
    print("   Email:    admin@parking.com")
    print("   Password: admin123")
    print("\n👤 TEST USER ACCOUNTS:")
    print("   Email:    john@gmail.com     | Password: john123")
    print("   Email:    jane@gmail.com     | Password: jane123")
    print("   Email:    test@gmail.com     | Password: test123")
    print("   Email:    rajesh@gmail.com   | Password: rajesh123")
    print("\n✅ You can now login with any of these accounts!")
else:
    print("\n⚠️  No new users were added.")

print("\n💡 Tip: Use admin@parking.com to access Scanner and Scan History!")
