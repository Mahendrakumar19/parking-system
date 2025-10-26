#!/usr/bin/env python3
"""
Reset and reinitialize parking spots with 20 bike slots and 20 car slots
"""

from app.database import Database
import os

def reset_parking_spots():
    print("🔄 Resetting parking spots to 20 bikes + 20 cars...")
    
    # Delete the database to start fresh
    if os.path.exists('parking.db'):
        os.remove('parking.db')
        print("✅ Deleted old database")
    
    # Reinitialize database
    db = Database()
    print("✅ Created new database")
    
    # Verify parking spots
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT slot_type, COUNT(*) FROM parking_spots GROUP BY slot_type')
    results = cursor.fetchall()
    
    print("\n📊 Parking Spots Summary:")
    for slot_type, count in results:
        print(f"  {slot_type.upper()}: {count} spots")
    
    # Show sample spots
    cursor.execute('SELECT spot_number, slot_type, zone FROM parking_spots ORDER BY slot_type, spot_number LIMIT 10')
    spots = cursor.fetchall()
    
    print("\n📋 Sample Parking Spots:")
    for spot in spots:
        print(f"  {spot[0]} ({spot[1]}) - Zone {spot[2]}")
    
    # Verify admins
    cursor.execute('SELECT username, name, role FROM admins')
    admins = cursor.fetchall()
    
    print("\n👤 Admin Users:")
    for admin in admins:
        print(f"  {admin[0]} ({admin[1]}) - Role: {admin[2]}")
    
    conn.close()
    print("\n✅ Database reset complete!")
    print("\n🎯 System Configuration:")
    print("  - Bike Slots: 20 (₹20/hour)")
    print("  - Car Slots: 20 (₹30/hour)")
    print("  - Admin: admin / admin123")
    print("  - Security: security / security123")

if __name__ == "__main__":
    reset_parking_spots()