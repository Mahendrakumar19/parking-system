import sqlite3
from datetime import datetime
import os

class Database:
    def __init__(self, db_path='parking.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                mobile TEXT NOT NULL,
                address TEXT NOT NULL,
                department TEXT NOT NULL,
                university_id TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Vehicles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                vehicle_number TEXT NOT NULL,
                vehicle_type TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Bookings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                vehicle_number TEXT NOT NULL,
                vehicle_type TEXT NOT NULL,
                entry_time TIMESTAMP NOT NULL,
                exit_time TIMESTAMP NOT NULL,
                actual_entry_time TIMESTAMP,
                actual_exit_time TIMESTAMP,
                amount DECIMAL(10,2) NOT NULL,
                status TEXT DEFAULT 'booked',
                qr_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Fines table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                booking_id TEXT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (booking_id) REFERENCES bookings (booking_id)
            )
        ''')
        
        # Admins table for security personnel
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'security',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Entry/Exit logs table for tracking vehicle movements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entry_exit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id TEXT NOT NULL,
                action_type TEXT NOT NULL,  -- 'entry' or 'exit'
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified_by TEXT,  -- admin who verified
                spot_number TEXT,
                status TEXT DEFAULT 'verified',
                FOREIGN KEY (booking_id) REFERENCES bookings (booking_id),
                FOREIGN KEY (verified_by) REFERENCES admins (admin_id)
            )
        ''')
        
        # Parking slots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parking_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slot_type TEXT NOT NULL,
                total_slots INTEGER NOT NULL,
                occupied_slots INTEGER DEFAULT 0
            )
        ''')
        
        # Individual parking spots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parking_spots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spot_number TEXT UNIQUE NOT NULL,
                slot_type TEXT NOT NULL,
                zone TEXT NOT NULL,
                floor_level INTEGER DEFAULT 1,
                is_occupied BOOLEAN DEFAULT 0,
                is_reserved BOOLEAN DEFAULT 0,
                current_booking_id TEXT,
                occupied_from TIMESTAMP,
                occupied_until TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'available',
                FOREIGN KEY (current_booking_id) REFERENCES bookings (booking_id)
            )
        ''')
        
        # Slot reservations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS slot_reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id TEXT NOT NULL,
                spot_number TEXT NOT NULL,
                reserved_from TIMESTAMP NOT NULL,
                reserved_until TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (booking_id) REFERENCES bookings (booking_id),
                FOREIGN KEY (spot_number) REFERENCES parking_spots (spot_number)
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                booking_id TEXT,
                transaction_type TEXT NOT NULL,
                parking_amount DECIMAL(10,2) DEFAULT 0,
                fine_amount DECIMAL(10,2) DEFAULT 0,
                extension_amount DECIMAL(10,2) DEFAULT 0,
                total_amount DECIMAL(10,2) NOT NULL,
                payment_method TEXT DEFAULT 'cash',
                transaction_status TEXT DEFAULT 'completed',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (booking_id) REFERENCES bookings (booking_id)
            )
        ''')
        
        # Initialize parking slots if empty
        cursor.execute('SELECT COUNT(*) FROM parking_slots')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO parking_slots (slot_type, total_slots) VALUES (?, ?)', ('bike', 50))
            cursor.execute('INSERT INTO parking_slots (slot_type, total_slots) VALUES (?, ?)', ('car', 30))
        
        # Initialize individual parking spots if empty
        cursor.execute('SELECT COUNT(*) FROM parking_spots')
        if cursor.fetchone()[0] == 0:
            self._initialize_parking_spots(cursor)
        
        # Initialize default admin (independent of parking slots)
        self._initialize_default_admin(cursor)
        
        conn.commit()
        conn.close()
    
    def _initialize_parking_spots(self, cursor):
        # Initialize bike spots (50 total)
        zones = ['A', 'B', 'C', 'D', 'E']
        for zone in zones:
            for i in range(1, 11):  # 10 spots per zone
                spot_number = f"B{zone}{i:02d}"  # B for bike, e.g., BA01, BA02, etc.
                cursor.execute('''
                    INSERT INTO parking_spots (spot_number, slot_type, zone, floor_level)
                    VALUES (?, ?, ?, ?)
                ''', (spot_number, 'bike', zone, 1))
        
        # Initialize car spots (30 total)
        zones = ['A', 'B', 'C']
        for zone in zones:
            for i in range(1, 11):  # 10 spots per zone
                spot_number = f"C{zone}{i:02d}"  # C for car, e.g., CA01, CA02, etc.
                cursor.execute('''
                    INSERT INTO parking_spots (spot_number, slot_type, zone, floor_level)
                    VALUES (?, ?, ?, ?)
                ''', (spot_number, 'car', zone, 1))
    
    def _initialize_default_admin(self, cursor):
        # Check if default admin already exists
        cursor.execute('SELECT COUNT(*) FROM admins WHERE username = ?', ('admin',))
        if cursor.fetchone()[0] == 0:
            import uuid
            admin_id = str(uuid.uuid4())[:8].upper()
            # Default admin credentials (username: admin, password: admin123)
            cursor.execute('''
                INSERT INTO admins (admin_id, username, password, name, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (admin_id, 'admin', 'admin123', 'System Administrator', 'admin'))
            
            # Security personnel
            security_id = str(uuid.uuid4())[:8].upper()
            cursor.execute('''
                INSERT INTO admins (admin_id, username, password, name, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (security_id, 'security', 'security123', 'Security Personnel', 'security'))
    
    def create_user(self, user_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Generate unique user ID
        import uuid
        user_id = str(uuid.uuid4())[:8].upper()
        
        cursor.execute('''
            INSERT INTO users (user_id, name, mobile, address, department, university_id, email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, user_data['name'], user_data['mobile'], user_data['address'],
              user_data['department'], user_data['university_id'], user_data['email']))
        
        conn.commit()
        conn.close()
        return user_id
    
    def get_user_by_id(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def check_slot_availability(self, vehicle_type, entry_time, exit_time):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get total slots for vehicle type
        cursor.execute('SELECT total_slots FROM parking_slots WHERE slot_type = ?', (vehicle_type,))
        total_slots = cursor.fetchone()[0]
        
        # Check overlapping bookings
        cursor.execute('''
            SELECT COUNT(*) FROM bookings 
            WHERE vehicle_type = ? AND status IN ('booked', 'active')
            AND ((entry_time <= ? AND exit_time > ?) OR 
                 (entry_time < ? AND exit_time >= ?) OR
                 (entry_time >= ? AND exit_time <= ?))
        ''', (vehicle_type, entry_time, entry_time, exit_time, exit_time, entry_time, exit_time))
        
        occupied = cursor.fetchone()[0]
        available = total_slots - occupied
        
        conn.close()
        return available
    
    def create_booking(self, booking_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bookings (booking_id, user_id, vehicle_number, vehicle_type, 
                                entry_time, exit_time, amount, qr_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (booking_data['booking_id'], booking_data['user_id'], booking_data['vehicle_number'],
              booking_data['vehicle_type'], booking_data['entry_time'],
              booking_data['exit_time'], booking_data['amount'], booking_data['qr_code']))
        
        conn.commit()
        conn.close()
        return booking_data['booking_id']
    
    def get_booking_by_id(self, booking_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bookings WHERE booking_id = ?', (booking_id,))
        booking = cursor.fetchone()
        conn.close()
        return booking
    
    def get_user_bookings(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM bookings WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        bookings = cursor.fetchall()
        conn.close()
        return bookings
    
    def get_pending_fines(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT SUM(amount) FROM fines 
            WHERE user_id = ? AND status = 'pending'
        ''', (user_id,))
        result = cursor.fetchone()[0]
        conn.close()
        return result if result else 0
    
    def add_fine(self, user_id, booking_id, amount, reason):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO fines (user_id, booking_id, amount, reason)
            VALUES (?, ?, ?, ?)
        ''', (user_id, booking_id, amount, reason))
        conn.commit()
        conn.close()
    
    def update_booking_status(self, booking_id, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE bookings SET status = ? WHERE booking_id = ?
        ''', (status, booking_id))
        conn.commit()
        conn.close()
    
    def update_entry_time(self, booking_id, entry_time):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE bookings SET actual_entry_time = ?, status = 'active' 
            WHERE booking_id = ?
        ''', (entry_time, booking_id))
        conn.commit()
        conn.close()
    
    def update_exit_time(self, booking_id, exit_time):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE bookings SET actual_exit_time = ?, status = 'completed' 
            WHERE booking_id = ?
        ''', (exit_time, booking_id))
        conn.commit()
        conn.close()
    
    def extend_booking_time(self, booking_id, new_exit_time, additional_amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Update the scheduled exit time and add to the amount
        cursor.execute('''
            UPDATE bookings 
            SET exit_time = ?, amount = amount + ?
            WHERE booking_id = ?
        ''', (new_exit_time, additional_amount, booking_id))
        
        conn.commit()
        conn.close()
    
    def pay_pending_fines(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE fines SET status = 'paid' 
            WHERE user_id = ? AND status = 'pending'
        ''', (user_id,))
        conn.commit()
        conn.close()
    
    def create_transaction(self, transaction_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        import uuid
        transaction_id = str(uuid.uuid4())[:16].upper()
        
        cursor.execute('''
            INSERT INTO transactions (transaction_id, user_id, booking_id, transaction_type,
                                    parking_amount, fine_amount, extension_amount, total_amount,
                                    payment_method, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (transaction_id, transaction_data['user_id'], transaction_data.get('booking_id'),
              transaction_data['transaction_type'], transaction_data.get('parking_amount', 0),
              transaction_data.get('fine_amount', 0), transaction_data.get('extension_amount', 0),
              transaction_data['total_amount'], transaction_data.get('payment_method', 'cash'),
              transaction_data.get('description', '')))
        
        conn.commit()
        conn.close()
        return transaction_id
    
    def get_transaction_by_id(self, transaction_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM transactions WHERE transaction_id = ?', (transaction_id,))
        transaction = cursor.fetchone()
        conn.close()
        return transaction
    
    def get_user_transactions(self, user_id, limit=10):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM transactions WHERE user_id = ? 
            ORDER BY created_at DESC LIMIT ?
        ''', (user_id, limit))
        transactions = cursor.fetchall()
        conn.close()
        return transactions
    
    def find_available_spot(self, vehicle_type, entry_time, exit_time):
        """Find the best available parking spot for the given time period"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Find spots that are available during the entire booking period
        cursor.execute('''
            SELECT spot_number, zone, floor_level FROM parking_spots 
            WHERE slot_type = ? AND status = 'available'
            AND spot_number NOT IN (
                SELECT spot_number FROM slot_reservations 
                WHERE status = 'active' 
                AND ((reserved_from <= ? AND reserved_until > ?) OR 
                     (reserved_from < ? AND reserved_until >= ?) OR
                     (reserved_from >= ? AND reserved_until <= ?))
            )
            ORDER BY zone, spot_number
            LIMIT 1
        ''', (vehicle_type, entry_time, entry_time, exit_time, exit_time, entry_time, exit_time))
        
        spot = cursor.fetchone()
        conn.close()
        return spot
    
    def reserve_parking_spot(self, booking_id, spot_number, entry_time, exit_time):
        """Reserve a specific parking spot for a booking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create reservation
        cursor.execute('''
            INSERT INTO slot_reservations (booking_id, spot_number, reserved_from, reserved_until)
            VALUES (?, ?, ?, ?)
        ''', (booking_id, spot_number, entry_time, exit_time))
        
        # Update parking spot status
        cursor.execute('''
            UPDATE parking_spots 
            SET is_reserved = 1, current_booking_id = ?, 
                occupied_from = ?, occupied_until = ?, last_updated = CURRENT_TIMESTAMP
            WHERE spot_number = ?
        ''', (booking_id, entry_time, exit_time, spot_number))
        
        conn.commit()
        conn.close()
    
    def occupy_parking_spot(self, booking_id, spot_number):
        """Mark a spot as occupied when vehicle enters"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE parking_spots 
            SET is_occupied = 1, status = 'occupied', last_updated = CURRENT_TIMESTAMP
            WHERE spot_number = ? AND current_booking_id = ?
        ''', (spot_number, booking_id))
        
        conn.commit()
        conn.close()
    
    def free_parking_spot(self, booking_id, spot_number):
        """Free up a parking spot when vehicle exits"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Update spot status
        cursor.execute('''
            UPDATE parking_spots 
            SET is_occupied = 0, is_reserved = 0, status = 'available',
                current_booking_id = NULL, occupied_from = NULL, 
                occupied_until = NULL, last_updated = CURRENT_TIMESTAMP
            WHERE spot_number = ? AND current_booking_id = ?
        ''', (spot_number, booking_id))
        
        # Update reservation status
        cursor.execute('''
            UPDATE slot_reservations 
            SET status = 'completed'
            WHERE booking_id = ? AND spot_number = ?
        ''', (booking_id, spot_number))
        
        conn.commit()
        conn.close()
    
    def get_parking_spot_by_booking(self, booking_id):
        """Get the parking spot assigned to a booking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ps.spot_number, ps.zone, ps.floor_level, ps.status, ps.is_occupied
            FROM parking_spots ps
            WHERE ps.current_booking_id = ?
        ''', (booking_id,))
        spot = cursor.fetchone()
        conn.close()
        return spot
    
    def get_live_parking_status(self, vehicle_type=None):
        """Get real-time parking availability status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if vehicle_type:
            cursor.execute('''
                SELECT 
                    zone,
                    COUNT(*) as total_spots,
                    SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available,
                    SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) as occupied,
                    SUM(CASE WHEN is_reserved = 1 AND is_occupied = 0 THEN 1 ELSE 0 END) as reserved
                FROM parking_spots 
                WHERE slot_type = ?
                GROUP BY zone
                ORDER BY zone
            ''', (vehicle_type,))
        else:
            cursor.execute('''
                SELECT 
                    slot_type,
                    zone,
                    COUNT(*) as total_spots,
                    SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available,
                    SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) as occupied,
                    SUM(CASE WHEN is_reserved = 1 AND is_occupied = 0 THEN 1 ELSE 0 END) as reserved
                FROM parking_spots 
                GROUP BY slot_type, zone
                ORDER BY slot_type, zone
            ''')
        
        status = cursor.fetchall()
        conn.close()
        return status
    
    def get_all_spots_with_status(self, vehicle_type=None):
        """Get all parking spots with their current status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if vehicle_type:
            cursor.execute('''
                SELECT spot_number, zone, floor_level, status, is_occupied, is_reserved,
                       current_booking_id, occupied_from, occupied_until
                FROM parking_spots 
                WHERE slot_type = ?
                ORDER BY zone, spot_number
            ''', (vehicle_type,))
        else:
            cursor.execute('''
                SELECT spot_number, slot_type, zone, floor_level, status, is_occupied, is_reserved,
                       current_booking_id, occupied_from, occupied_until
                FROM parking_spots 
                ORDER BY slot_type, zone, spot_number
            ''')
        
        spots = cursor.fetchall()
        conn.close()
        return spots
    
    def extend_spot_reservation(self, booking_id, new_exit_time):
        """Extend the reservation time for a parking spot"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Update reservation
        cursor.execute('''
            UPDATE slot_reservations 
            SET reserved_until = ?
            WHERE booking_id = ? AND status = 'active'
        ''', (new_exit_time, booking_id))
        
        # Update parking spot
        cursor.execute('''
            UPDATE parking_spots 
            SET occupied_until = ?, last_updated = CURRENT_TIMESTAMP
            WHERE current_booking_id = ?
        ''', (new_exit_time, booking_id))
        
        conn.commit()
        conn.close()
    
    # Admin authentication methods
    def authenticate_admin(self, username, password):
        """Authenticate admin user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT admin_id, name, role FROM admins 
            WHERE username = ? AND password = ?
        ''', (username, password))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'admin_id': result[0],
                'name': result[1],
                'role': result[2],
                'username': username
            }
        return None
    
    def get_admin_by_id(self, admin_id):
        """Get admin details by admin_id"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT admin_id, username, name, role FROM admins 
            WHERE admin_id = ?
        ''', (admin_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'admin_id': result[0],
                'username': result[1],
                'name': result[2],
                'role': result[3]
            }
        return None
    
    # QR Code verification methods
    def verify_qr_booking(self, booking_id):
        """Verify if booking exists and get details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.*, u.name, u.mobile, ps.spot_number, ps.zone, ps.floor_level
            FROM bookings b
            JOIN users u ON b.user_id = u.user_id
            LEFT JOIN slot_reservations sr ON b.booking_id = sr.booking_id AND sr.status = 'active'
            LEFT JOIN parking_spots ps ON sr.spot_number = ps.spot_number
            WHERE b.booking_id = ? AND b.status IN ('booked', 'active')
        ''', (booking_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'booking_id': result[1],
                'user_id': result[2],
                'vehicle_number': result[3],
                'vehicle_type': result[4],
                'entry_time': result[5],
                'exit_time': result[6],
                'amount': result[8],
                'status': result[9],
                'user_name': result[12],
                'user_mobile': result[13],
                'spot_number': result[14],
                'zone': result[15],
                'floor_level': result[16]
            }
        return None
    
    def record_entry_exit(self, booking_id, action_type, admin_id, spot_number=None):
        """Record entry or exit action"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO entry_exit_logs (booking_id, action_type, verified_by, spot_number)
            VALUES (?, ?, ?, ?)
        ''', (booking_id, action_type, admin_id, spot_number))
        
        # Update booking status if needed
        if action_type == 'entry':
            cursor.execute('''
                UPDATE bookings SET status = 'active' WHERE booking_id = ?
            ''', (booking_id,))
            
            # Occupy the parking spot
            if spot_number:
                cursor.execute('''
                    UPDATE parking_spots 
                    SET is_occupied = 1, current_booking_id = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE spot_number = ?
                ''', (booking_id, spot_number))
                
        elif action_type == 'exit':
            cursor.execute('''
                UPDATE bookings SET status = 'completed' WHERE booking_id = ?
            ''', (booking_id,))
            
            # Free the parking spot
            if spot_number:
                cursor.execute('''
                    UPDATE parking_spots 
                    SET is_occupied = 0, current_booking_id = NULL, occupied_until = NULL, last_updated = CURRENT_TIMESTAMP
                    WHERE spot_number = ?
                ''', (spot_number,))
                
                # Mark reservation as completed
                cursor.execute('''
                    UPDATE slot_reservations 
                    SET status = 'completed'
                    WHERE booking_id = ? AND status = 'active'
                ''', (booking_id,))
        
        conn.commit()
        conn.close()
        return True
    
    def get_entry_exit_logs(self, booking_id=None, limit=100):
        """Get entry/exit logs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if booking_id:
            cursor.execute('''
                SELECT eel.*, b.vehicle_number, b.vehicle_type, u.name as user_name, a.name as admin_name
                FROM entry_exit_logs eel
                JOIN bookings b ON eel.booking_id = b.booking_id
                JOIN users u ON b.user_id = u.user_id
                JOIN admins a ON eel.verified_by = a.admin_id
                WHERE eel.booking_id = ?
                ORDER BY eel.timestamp DESC
            ''', (booking_id,))
        else:
            cursor.execute('''
                SELECT eel.*, b.vehicle_number, b.vehicle_type, u.name as user_name, a.name as admin_name
                FROM entry_exit_logs eel
                JOIN bookings b ON eel.booking_id = b.booking_id
                JOIN users u ON b.user_id = u.user_id
                JOIN admins a ON eel.verified_by = a.admin_id
                ORDER BY eel.timestamp DESC
                LIMIT ?
            ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in results:
            logs.append({
                'id': row[0],
                'booking_id': row[1],
                'action_type': row[2],
                'timestamp': row[3],
                'verified_by': row[4],
                'spot_number': row[5],
                'status': row[6],
                'vehicle_number': row[7],
                'vehicle_type': row[8],
                'user_name': row[9],
                'admin_name': row[10]
            })
        
        return logs
    
    def check_duplicate_entry_exit(self, booking_id, action_type):
        """Check if entry/exit has already been recorded"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM entry_exit_logs 
            WHERE booking_id = ? AND action_type = ?
        ''', (booking_id, action_type))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0