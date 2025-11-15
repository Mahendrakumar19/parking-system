import sqlite3

conn = sqlite3.connect('backend/database/parking.db')
cursor = conn.cursor()

cursor.execute('SELECT booking_id, status, actual_exit_time FROM bookings ORDER BY id DESC LIMIT 10')

print("\nRecent bookings:")
print("-" * 70)
for row in cursor.fetchall():
    print(f"ID: {row[0]:15} | Status: {row[1]:12} | Exit: {row[2]}")

conn.close()
