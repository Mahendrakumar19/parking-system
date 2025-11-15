import sqlite3
import sys

# Connect to database
conn = sqlite3.connect('backend/database/parking.db')
cursor = conn.cursor()

# Get booking ID from command line or use default
booking_id = sys.argv[1] if len(sys.argv) > 1 else 'BK8C221A43'

print(f"\n🗑️  Deleting booking: {booking_id}")

# Delete the booking
cursor.execute('DELETE FROM bookings WHERE booking_id = ?', (booking_id,))
booking_deleted = cursor.rowcount
conn.commit()

print(f"✅ Deleted {booking_deleted} booking(s)")

# Also delete related gate scans if any
cursor.execute('DELETE FROM gate_scans WHERE booking_id = ?', (booking_id,))
scans_deleted = cursor.rowcount
conn.commit()

print(f"✅ Deleted {scans_deleted} gate scan(s)")

# Show remaining bookings
cursor.execute('SELECT booking_id, status FROM bookings ORDER BY id DESC LIMIT 5')
print(f"\n📋 Recent bookings:")
for row in cursor.fetchall():
    print(f"   - {row[0]} ({row[1]})")

conn.close()
print("\n✅ Done!")
