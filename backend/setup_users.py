"""
Initialize Database and Create Predefined Users
This script initializes the database and creates test accounts
"""
import sqlite3
import hashlib
import os
import sys

# Add parent directory to path to import from app.py
sys.path.insert(0, os.path.dirname(__file__))

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

print("🔄 Initializing database...")

# Import and run database initialization from app.py
try:
    from app import init_db
    init_db()
    print("✅ Database initialized successfully!")
except ImportError as e:
    print(f"❌ Error importing app module: {e}")
    sys.exit(1)

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'database', 'parking.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\n🔐 Creating predefined user accounts...\n")

# Predefined users
users = [
    {
        'name': 'Admin User',
        'mobile': '9999999999',
        'address': 'Admin Office, University Campus',
        'department': 'Administration',
        'university_id': 'ADMIN001',
        'email': 'admin@parking.com',
        'password': 'admin123'
    },
    {
        'name': 'John Doe',
        'mobile': '9876543210',
        'address': '123 Main Street, City',
        'department': 'Computer Science',
        'university_id': 'STU001',
        'email': 'john@gmail.com',
        'password': 'john123'
    },
    {
        'name': 'Jane Smith',
        'mobile': '9876543211',
        'address': '456 Park Avenue, City',
        'department': 'Electrical Engineering',
        'university_id': 'STU002',
        'email': 'jane@gmail.com',
        'password': 'jane123'
    },
    {
        'name': 'Test User',
        'mobile': '9876543212',
        'address': '789 College Road, City',
        'department': 'Mechanical Engineering',
        'university_id': 'STU003',
        'email': 'test@gmail.com',
        'password': 'test123'
    },
    {
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
user_id_counter = 1

for user in users:
    try:
        # Check if user already exists
        cursor.execute("SELECT email FROM users WHERE email = ?", (user['email'],))
        if cursor.fetchone():
            print(f"⚠️  Skipped: {user['email']} (already exists)")
            skipped_count += 1
            continue
        
        # Generate user_id
        user_id = f'U{str(user_id_counter).zfill(3)}'
        user_id_counter += 1
        
        # Insert user
        cursor.execute('''
            INSERT INTO users (user_id, name, mobile, address, department, university_id, email, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
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
        print(f"   User ID: {user_id} | Password: {user['password']}")
        added_count += 1
        
    except sqlite3.IntegrityError as e:
        print(f"⚠️  Skipped: {user['email']} ({e})")
        skipped_count += 1
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
    print("\n👑 ADMIN ACCOUNT (Full Access - Scanner & All Bookings):")
    print("   Email:    admin@parking.com")
    print("   Password: admin123")
    print("\n👤 TEST USER ACCOUNTS:")
    print("   Email:    john@gmail.com     | Password: john123")
    print("   Email:    jane@gmail.com     | Password: jane123")
    print("   Email:    test@gmail.com     | Password: test123")
    print("   Email:    rajesh@gmail.com   | Password: rajesh123")
    print("\n✅ You can now login at: http://localhost:5000")
    print("\n💡 Tips:")
    print("   - Use admin@parking.com to access Scanner and Scan History")
    print("   - Regular users can book slots and view their own bookings")
    print("   - Start the server: python app.py")
else:
    print("\n⚠️  No new users were added.")
