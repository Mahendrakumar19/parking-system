from validate_card import validate_debit_card_details
from validate_car import validate_old_indian_car_number
from validate_bike import validate_indian_plate
from qr_system import QRCodeSystem, DeviceScanner
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import sqlite3
import os
import sys
from datetime import datetime, timedelta
import hashlib
import secrets
import re
import json

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Database path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'parking.db')

# Ensure database directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize QR Code System
qr_system = QRCodeSystem()

# Initialize virtual device scanners (simulating physical devices)
entry_scanner = DeviceScanner('ENTRY-001', 'Main Gate - Entry', 'entry')
exit_scanner = DeviceScanner('EXIT-001', 'Main Gate - Exit', 'exit')

# Database setup


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            mobile VARCHAR(15) NOT NULL,
            address TEXT NOT NULL,
            department VARCHAR(50) NOT NULL,
            university_id VARCHAR(20) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id VARCHAR(20) UNIQUE NOT NULL,
            user_id VARCHAR(20) NOT NULL,
            vehicle_type VARCHAR(10) NOT NULL,
            vehicle_number VARCHAR(20) NOT NULL,
            entry_time DATETIME NOT NULL,
            exit_time DATETIME NOT NULL,
            actual_entry_time DATETIME,
            actual_exit_time DATETIME,
            duration_hours INTEGER NOT NULL,
            cost DECIMAL(10,2) NOT NULL,
            payment_status VARCHAR(20) DEFAULT 'pending',
            status VARCHAR(20) DEFAULT 'confirmed',
            qr_code TEXT,
            scan_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create gate scans table for tracking entry/exit
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gate_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id VARCHAR(20) NOT NULL,
            gate_type VARCHAR(10) NOT NULL,
            vehicle_number VARCHAR(20) NOT NULL,
            scan_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            success BOOLEAN NOT NULL,
            overstay BOOLEAN DEFAULT 0,
            additional_charge DECIMAL(10,2) DEFAULT 0,
            message TEXT
        )
    ''')

    # Create admin notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type VARCHAR(50) NOT NULL,
            booking_id VARCHAR(20),
            user_id VARCHAR(20),
            user_name VARCHAR(100),
            user_email VARCHAR(100),
            vehicle_type VARCHAR(10),
            vehicle_number VARCHAR(20),
            entry_time DATETIME,
            exit_time DATETIME,
            cost DECIMAL(10,2),
            message TEXT,
            read_status BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

# Password hashing


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Generate unique IDs


def generate_booking_id():
    return 'BK' + secrets.token_hex(4).upper()

# API Routes


@app.route('/api/register', methods=['POST'])
def register():
    data = request.json

    # Validation
    errors = []

    # Name validation (alphabets only)
    if 'name' in data:
        if not re.match(r'^[A-Za-z\s]+$', data['name']):
            errors.append('Name must contain only alphabets and spaces')

    # Mobile validation (10 digits)
    if 'mobile' in data:
        if not re.match(r'^\d{10}$', data['mobile']):
            errors.append('Mobile number must be exactly 10 digits')

    # University ID validation (alphanumeric only)
    if 'university_id' in data or 'universityId' in data:
        university_id = data.get('university_id') or data.get('universityId')
        if not re.match(r'^[A-Za-z0-9]+$', university_id):
            errors.append('University ID must be alphanumeric only')

    # Email validation
    if 'email' in data:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            errors.append('Invalid email format')

    # Password validation (min 8 chars, 1 uppercase, 1 lowercase, 1 special)
    if 'password' in data:
        password = data['password']
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', password):
            errors.append(
                'Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', password):
            errors.append(
                'Password must contain at least one lowercase letter')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append(
                'Password must contain at least one special character')

    if errors:
        return jsonify({
            'success': False,
            'message': 'Validation errors',
            'errors': errors
        }), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        password_hash = hash_password(data['password'])

        # Handle both 'university_id' and 'universityId' field names
        university_id = data.get('university_id') or data.get('universityId')

        # Generate unique user_id (e.g., U001, U002, etc.)
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        user_id = f'U{str(user_count + 1).zfill(3)}'  # U001, U002, U003, etc.

        # Insert new user with generated user_id
        cursor.execute('''
            INSERT INTO users (user_id, name, mobile, address, department, university_id, email, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,  # Use generated user_id instead of email
            data['name'],
            data['mobile'],
            data['address'],
            data['department'],
            university_id,
            data['email'],
            password_hash
        ))

        conn.commit()
        return jsonify({
            'success': True,
            'message': 'Registration successful'
        })

    except sqlite3.IntegrityError as e:
        return jsonify({
            'success': False,
            'message': 'Email or University ID already exists'
        }), 400

    finally:
        conn.close()


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Login with email and password
    email = data.get('email')
    password = data.get('password')

    cursor.execute('''
        SELECT user_id, name, email FROM users 
        WHERE email = ? AND password_hash = ?
    ''', (email, hash_password(password)))

    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            'success': True,
            'user': {
                'userid': user[0],
                'name': user[1],
                'email': user[2]
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid email or password'
        }), 401


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for scanner and frontend"""
    return jsonify({
        'status': 'online',
        'message': 'Server is running',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/api/admin-notification', methods=['POST'])
def admin_notification():
    """Receive and store admin notifications for new bookings"""
    try:
        data = request.json
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create a readable message
        message = f"New booking by {data.get('user_name')} - {data.get('vehicle_type').upper()} ({data.get('vehicle_number')})"
        
        cursor.execute('''
            INSERT INTO admin_notifications 
            (type, booking_id, user_id, user_name, user_email, vehicle_type, 
             vehicle_number, entry_time, exit_time, cost, message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('type'),
            data.get('booking_id'),
            data.get('user_id'),
            data.get('user_name'),
            data.get('user_email'),
            data.get('vehicle_type'),
            data.get('vehicle_number'),
            data.get('entry_time'),
            data.get('exit_time'),
            data.get('cost'),
            message
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Admin notified successfully'
        }), 200
        
    except Exception as e:
        print(f"Admin notification error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/check-availability', methods=['POST'])
def check_availability():
    data = request.json

    # Simple check - parking is available (no slot tracking)
    return jsonify({
        'available': True,
        'vehicle_type': data['vehicle_type']
    })


@app.route('/api/book-slot', methods=['POST'])
def book_slot():
    data = request.json

    # Validate vehicle number based on vehicle type
    vehicle_type = data.get('vehicle_type')
    vehicle_number = data.get('vehicle_number')

    if vehicle_type == 'bike':
        if not validate_indian_plate(vehicle_number):
            return jsonify({
                'success': False,
                'message': 'Invalid bike number plate format. Expected format: MH 03 AA 4567 or MH03AA4567'
            }), 400
    elif vehicle_type == 'car':
        if not validate_old_indian_car_number(vehicle_number):
            return jsonify({
                'success': False,
                'message': 'Invalid car number plate format. Expected format: GJ 03 AY 1097 or GJ03AY1097'
            }), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Don't assign slot during booking - it will be assigned at entry scan
        booking_id = generate_booking_id()

        # Calculate cost
        rate = 20 if data['vehicle_type'] == 'bike' else 30
        cost = data['duration_hours'] * rate
        
        # Normalize datetime formats from HTML datetime-local (2025-10-28T22:13) to standard format
        def normalize_datetime(dt_str):
            # Remove timezone info and microseconds if present
            dt_str = dt_str.split('.')[0]  # Remove microseconds
            dt_str = dt_str.replace('Z', '')  # Remove UTC indicator
            dt_str = dt_str.split('+')[0]  # Remove timezone offset
            
            # Try different datetime formats
            if 'T' in dt_str:
                # HTML datetime-local format: 2025-10-28T22:13 or ISO format
                try:
                    dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
                except ValueError:
                    dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M')
            else:
                # Standard format: 2025-10-28 22:13:00
                try:
                    dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        
        entry_time_normalized = normalize_datetime(data['entry_time'])
        exit_time_normalized = normalize_datetime(data['exit_time'])

        # Generate secure QR code
        qr_result = qr_system.generate_qr_code(
            booking_id=booking_id,
            user_id=data['user_id'],
            vehicle_number=data['vehicle_number'],
            vehicle_type=data['vehicle_type'],
            entry_time=entry_time_normalized,
            exit_time=exit_time_normalized,
            slot_number=None
        )

        # Insert booking
        cursor.execute('''
            INSERT INTO bookings (booking_id, user_id, vehicle_type, vehicle_number, 
                                entry_time, exit_time, duration_hours, cost, qr_code, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'paid')
        ''', (
            booking_id,
            data['user_id'],
            data['vehicle_type'],
            data['vehicle_number'],
            entry_time_normalized,
            exit_time_normalized,
            data['duration_hours'],
            cost,
            qr_result['qr_string']
        ))

        conn.commit()

        return jsonify({
            'success': True,
            'booking_id': booking_id,
            'cost': cost,
            'qr_code': qr_result['qr_code_image'],
            'qr_data': qr_result['qr_string'],
            'message': 'Booking confirmed! Scan QR at entry gate.'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

    finally:
        conn.close()


@app.route('/api/extend-booking', methods=['POST'])
def extend_booking():
    """Extend an existing booking by adding more hours"""
    data = request.json
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        booking_id = data['booking_id']
        extend_hours = int(data['extend_hours'])
        
        # Get current booking details
        cursor.execute('''
            SELECT booking_id, vehicle_type, exit_time, duration_hours, cost
            FROM bookings 
            WHERE booking_id = ?
        ''', (booking_id,))
        
        booking = cursor.fetchone()
        if not booking:
            return jsonify({'success': False, 'message': 'Booking not found'}), 404
        
        bk_id, vehicle_type, current_exit, current_duration, current_cost = booking
        
        # Calculate additional cost
        rate = 20 if vehicle_type == 'bike' else 30
        additional_cost = extend_hours * rate
        new_total_cost = current_cost + additional_cost
        new_duration = current_duration + extend_hours
        
        # Calculate new exit time
        from datetime import datetime, timedelta
        current_exit_dt = datetime.strptime(current_exit, '%Y-%m-%d %H:%M:%S')
        new_exit_dt = current_exit_dt + timedelta(hours=extend_hours)
        new_exit_time = new_exit_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Update booking with new exit time and cost
        cursor.execute('''
            UPDATE bookings 
            SET exit_time = ?, duration_hours = ?, cost = ?
            WHERE booking_id = ?
        ''', (new_exit_time, new_duration, new_total_cost, booking_id))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'Booking extended by {extend_hours} hours',
            'additional_cost': additional_cost,
            'new_total_cost': new_total_cost,
            'new_exit_time': new_exit_time,
            'new_duration': new_duration
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    
    finally:
        conn.close()


@app.route('/api/user-bookings/<user_id>')
def get_user_bookings(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get bookings without slot information
        cursor.execute('''
            SELECT b.*
            FROM bookings b
            WHERE b.user_id = ? 
            ORDER BY b.id DESC
        ''', (user_id,))

        bookings = cursor.fetchall()

        # Convert to simplified list with only essential fields
        booking_list = []
        for booking in bookings:
            booking_dict = {
                'booking_id': booking[1],
                'vehicle_type': booking[3],
                'vehicle_number': booking[4],
                'entry_time': booking[5],  # Scheduled entry
                'exit_time': booking[6],   # Scheduled exit
                'actual_entry_time': booking[7],  # Actual entry (from scan)
                'actual_exit_time': booking[8],   # Actual exit (from scan)
                'duration_hours': booking[9],
                'cost': booking[10],
                'status': booking[12] if len(booking) > 12 else 'unknown'
            }
            booking_list.append(booking_dict)

        return jsonify(booking_list)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        conn.close()


@app.route('/api/cancel-booking/<booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    """Cancel a confirmed booking (not yet entered)"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if booking exists and belongs to user
        cursor.execute('''
            SELECT status, actual_entry_time FROM bookings 
            WHERE booking_id = ? AND user_id = ?
        ''', (booking_id, user_id))
        
        booking = cursor.fetchone()
        
        if not booking:
            return jsonify({
                'success': False,
                'message': 'Booking not found or unauthorized'
            }), 404
        
        status, actual_entry = booking
        
        # Only allow cancellation of confirmed bookings (not yet entered)
        if status != 'confirmed':
            return jsonify({
                'success': False,
                'message': 'Can only cancel bookings that haven\'t been used yet'
            }), 400
        
        if actual_entry:
            return jsonify({
                'success': False,
                'message': 'Cannot cancel - vehicle already entered'
            }), 400
        
        # Update booking status to cancelled
        cursor.execute('''
            UPDATE bookings SET status = 'cancelled'
            WHERE booking_id = ?
        ''', (booking_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Booking cancelled successfully'
        })
        
    except Exception as e:
        print(f"Error cancelling booking: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/all-bookings')
def get_all_bookings():
    """Get all bookings with optional filters - Admin only"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get filter parameters
        email_filter = request.args.get('email', '').strip()
        vehicle_filter = request.args.get('vehicle_number', '').strip()
        status_filter = request.args.get('status', '').strip()

        # Build query with filters
        query = '''
            SELECT b.*, u.name, u.email
            FROM bookings b
            LEFT JOIN users u ON b.user_id = u.user_id
            WHERE 1=1
        '''
        params = []

        if email_filter:
            query += ' AND u.email LIKE ?'
            params.append(f'%{email_filter}%')
        
        if vehicle_filter:
            query += ' AND b.vehicle_number LIKE ?'
            params.append(f'%{vehicle_filter}%')
        
        if status_filter:
            query += ' AND b.status = ?'
            params.append(status_filter)

        # Check if created_at column exists
        cursor.execute("PRAGMA table_info(bookings)")
        columns = [col[1] for col in cursor.fetchall()]
        order_by = 'b.created_at DESC' if 'created_at' in columns else 'b.id DESC'
        query += f' ORDER BY {order_by}'

        cursor.execute(query, params)
        bookings = cursor.fetchall()

        # Convert to list of dictionaries with simplified data
        booking_list = []
        for booking in bookings:
            booking_dict = {
                'booking_id': booking[1],
                'vehicle_type': booking[3],
                'vehicle_number': booking[4],
                'entry_time': booking[5],  # Scheduled entry
                'exit_time': booking[6],   # Scheduled exit
                'actual_entry_time': booking[7],  # Actual entry (from scan)
                'actual_exit_time': booking[8],   # Actual exit (from scan)
                'duration_hours': booking[9],
                'cost': booking[10],
                'status': booking[12] if len(booking) > 12 else 'unknown',
                'user_name': booking[16] if len(booking) > 16 else 'N/A',
                'user_email': booking[17] if len(booking) > 17 else 'N/A'
            }
            booking_list.append(booking_dict)

        return jsonify({'bookings': booking_list})

    except Exception as e:
        print(f"Error fetching all bookings: {str(e)}")
        return jsonify({'error': str(e)}), 500

    finally:
        conn.close()


@app.route('/api/validate-payment', methods=['POST'])
def validate_payment():
    data = request.json

    card_number = data.get('card_number', '').strip()
    cvv = data.get('cvv', '').strip()
    name = data.get('card_name', '').strip()
    expiry_date = data.get('expiry_date', '').strip()

    # Validate card details
    is_card_valid, is_cvv_valid, is_name_valid, is_expiry_valid = validate_debit_card_details(
        card_number, cvv, name, expiry_date)

    errors = []
    if not is_card_valid:
        errors.append(
            'Invalid card number. Use a valid 16-digit Visa, Mastercard, or RuPay card')
    if not is_cvv_valid:
        errors.append('Invalid CVV. CVV must be exactly 3 digits')
    if not is_name_valid:
        errors.append(
            'Invalid name. Name can only contain alphabets and spaces')
    if not is_expiry_valid:
        errors.append(
            'Invalid expiry date. Use MM/YY format and ensure it is not expired')

    if errors:
        return jsonify({
            'success': False,
            'message': 'Payment validation failed',
            'errors': errors
        }), 400

    return jsonify({
        'success': True,
        'message': 'Card details validated successfully'
    })


@app.route('/api/dashboard-stats')
def dashboard_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Count active bookings by vehicle type to show "available" slots
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = 'in_progress' AND vehicle_type = 'bike'")
    bike_in_use = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = 'in_progress' AND vehicle_type = 'car'")
    car_in_use = cursor.fetchone()[0]

    # Show available slots (total capacity - in use)
    bike_slots = max(0, 50 - bike_in_use)
    car_slots = max(0, 30 - car_in_use)

    # Active bookings today
    cursor.execute(
        "SELECT COUNT(*) FROM bookings WHERE DATE(entry_time) = DATE('now') AND status IN ('confirmed', 'in_progress')")
    active_bookings = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        'bike_slots': bike_slots,
        'car_slots': car_slots,
        'active_bookings': active_bookings
    })


# ========== QR CODE & DEVICE SCANNER APIs ==========

@app.route('/api/qr/scan-entry', methods=['POST'])
def scan_entry():
    """Simulate scanning QR code at entry gate"""
    data = request.json
    qr_data = data.get('qr_data')
    
    if not qr_data:
        return jsonify({
            'success': False,
            'message': 'No QR data provided'
        }), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Validate QR code
        qr_system = QRCodeSystem()
        validation = qr_system.validate_qr_code(qr_data)
        
        if not validation['valid']:
            return jsonify({'success': False, 'message': validation['message']}), 400
        
        booking_id = validation['booking_id']
        
        # Check booking and scan count - get user_id too
        cursor.execute('''
            SELECT booking_id, vehicle_number, scan_count, actual_entry_time, user_id
            FROM bookings 
            WHERE booking_id = ?
        ''', (booking_id,))
        
        booking = cursor.fetchone()
        
        if not booking:
            return jsonify({'success': False, 'message': 'Booking not found'}), 404
        
        # Unpack tuple properly
        bk_id, vehicle_num, scan_count, actual_entry, user_id = booking
        scan_count = scan_count if scan_count is not None else 0
        
        # Check if already scanned 2 times
        if scan_count >= 2:
            return jsonify({
                'success': False, 
                'message': 'QR code expired - already used 2 times (entry & exit)'
            }), 400
        
        # Check if already entered but not exited
        if scan_count == 1 and actual_entry:
            return jsonify({
                'success': False, 
                'message': 'Vehicle already entered. Please scan at exit gate.'
            }), 400
        
        # Record entry
        current_time = datetime.now()
        cursor.execute('''
            UPDATE bookings 
            SET actual_entry_time = ?, scan_count = scan_count + 1, status = 'in_progress'
            WHERE booking_id = ?
        ''', (current_time.strftime('%Y-%m-%d %H:%M:%S'), booking_id))
        
        # Store scan record
        cursor.execute('''
            INSERT INTO gate_scans (booking_id, gate_type, vehicle_number, success, message)
            VALUES (?, 'entry', ?, ?, ?)
        ''', (booking_id, vehicle_num, True, 'Entry authorized'))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': '✅ Entry Authorized',
            'gate_action': 'OPEN GATE',
            'vehicle_number': vehicle_num,
            'entry_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'scans_remaining': 1
        })
        
    except Exception as e:
        print(f"Error processing entry scan: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/qr/scan-exit', methods=['POST'])
def scan_exit():
    """Simulate scanning QR code at exit gate"""
    data = request.json
    qr_data = data.get('qr_data')
    
    if not qr_data:
        return jsonify({
            'success': False,
            'message': 'No QR data provided'
        }), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Validate QR code
        qr_system = QRCodeSystem()
        validation = qr_system.validate_qr_code(qr_data)
        
        if not validation['valid']:
            return jsonify({'success': False, 'message': validation['message']}), 400
        
        booking_id = validation['booking_id']
        
        # Check booking and scan count - get user_id too
        cursor.execute('''
            SELECT booking_id, vehicle_number, scan_count, actual_entry_time, actual_exit_time, 
                   exit_time, cost, user_id, duration_hours
            FROM bookings 
            WHERE booking_id = ?
        ''', (booking_id,))
        
        booking = cursor.fetchone()
        
        if not booking:
            return jsonify({'success': False, 'message': 'Booking not found'}), 404
        
        # Unpack tuple properly
        bk_id, vehicle_num, scan_count, actual_entry_time, actual_exit_time, scheduled_exit, base_cost, user_id, duration_hours = booking
        scan_count = scan_count if scan_count is not None else 0
        
        # Check if already scanned 2 times
        if scan_count >= 2:
            return jsonify({
                'success': False, 
                'message': 'QR code expired - already used 2 times (entry & exit)'
            }), 400
        
        # Check if vehicle has entered
        if not actual_entry_time:
            return jsonify({
                'success': False, 
                'message': 'Vehicle has not entered yet. Please scan at entry gate first.'
            }), 400
        
        # Check if already exited
        if actual_exit_time:
            return jsonify({
                'success': False, 
                'message': 'Vehicle already exited.'
            }), 400
        
        # Record exit
        current_time = datetime.now()
        entry_dt = datetime.strptime(actual_entry_time, '%Y-%m-%d %H:%M:%S')
        
        # Calculate actual duration (from actual entry to actual exit)
        actual_duration_minutes = (current_time - entry_dt).total_seconds() / 60
        actual_duration_hours = actual_duration_minutes / 60
        
        # Calculate overstay based on booked duration
        booked_duration = duration_hours  # This is what they paid for
        overstay = False
        additional_charge = 0
        overstay_hours = 0
        
        # Only charge overstay if they stayed longer than booked hours
        if actual_duration_hours > booked_duration:
            overstay = True
            extra_hours = actual_duration_hours - booked_duration
            # Round up to next hour for overstay charges
            overstay_hours = int(extra_hours) + (1 if extra_hours % 1 > 0 else 0)
            additional_charge = overstay_hours * 20  # ₹20 per extra hour
        
        total_cost = base_cost + additional_charge
        
        # Update booking
        cursor.execute('''
            UPDATE bookings 
            SET actual_exit_time = ?, scan_count = scan_count + 1, status = 'completed',
                cost = ?
            WHERE booking_id = ?
        ''', (current_time.strftime('%Y-%m-%d %H:%M:%S'), total_cost, booking_id))
        
        # Store scan record
        cursor.execute('''
            INSERT INTO gate_scans (booking_id, gate_type, vehicle_number, success, overstay, additional_charge, message)
            VALUES (?, 'exit', ?, ?, ?, ?, ?)
        ''', (booking_id, vehicle_num, True, overstay, additional_charge,
              f'Exit authorized{" - OVERSTAY DETECTED" if overstay else ""}'))
        
        conn.commit()
        
        result = {
            'success': True,
            'message': '✅ Exit Authorized' + (' - OVERSTAY DETECTED ⚠️' if overstay else ''),
            'gate_action': 'OPEN GATE',
            'vehicle_number': vehicle_num,
            'entry_time': actual_entry_time,
            'exit_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'overstay': overstay,
            'total_cost': total_cost,
            'scans_remaining': 0
        }
        
        if overstay:
            result['overstay_hours'] = overstay_hours
            result['additional_charge'] = additional_charge
            result['base_cost'] = base_cost
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error processing exit scan: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()
    
    # Store scan record in database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Insert gate scan record with overstay info
        cursor.execute('''
            INSERT INTO gate_scans (booking_id, gate_type, vehicle_number, success, overstay, additional_charge, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            result.get('booking_id', 'N/A'),
            'exit',
            result.get('vehicle_number', 'Unknown'),
            result['success'],
            result.get('overstay', False),
            result.get('additional_charge', 0),
            result.get('message', '')
        ))
        
        # If exit is authorized, complete booking
        if result['success']:
            # Complete the booking
            cursor.execute('''
                UPDATE bookings 
                SET status = 'completed'
                WHERE booking_id = ?
            ''', (result['booking_id'],))
        
        conn.commit()
    except Exception as e:
        print(f"Error completing exit: {e}")
        result['warning'] = 'Exit allowed but booking completion failed'
    finally:
        conn.close()
    
    return jsonify(result)


@app.route('/api/qr/get-booking-qr/<booking_id>')
def get_booking_qr(booking_id):
    """Get QR code for a specific booking"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT booking_id, user_id, vehicle_type, vehicle_number, 
                   entry_time, exit_time, qr_code
            FROM bookings 
            WHERE booking_id = ?
        ''', (booking_id,))
        
        booking = cursor.fetchone()
        
        if not booking:
            return jsonify({
                'success': False,
                'message': 'Booking not found'
            }), 404
        
        # Parse QR data to get the image
        qr_data_str = booking[6]
        
        # Regenerate QR image
        qr_result = qr_system.generate_qr_code(
            booking_id=booking[0],
            user_id=booking[1],
            vehicle_number=booking[3],
            vehicle_type=booking[2],
            entry_time=booking[4],
            exit_time=booking[5],
            slot_number=None
        )
        
        return jsonify({
            'success': True,
            'booking_id': booking[0],
            'vehicle_number': booking[3],
            'qr_code': qr_result['qr_code_image'],
            'qr_data': qr_result['qr_string'],
            'vehicle_type': booking[2],
            'entry_time': booking[4],
            'exit_time': booking[5]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        conn.close()


@app.route('/api/device/scan-history/<device_type>')
def get_scan_history(device_type):
    """Get scan history for entry or exit device"""
    if device_type == 'entry':
        history = entry_scanner.get_scan_history(20)
    elif device_type == 'exit':
        history = exit_scanner.get_scan_history(20)
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid device type'
        }), 400
    
    return jsonify({
        'success': True,
        'device_type': device_type,
        'scan_history': history
    })


@app.route('/api/scan-history', methods=['GET'])
def get_all_scan_history():
    """Get complete scan history from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        user_id = request.args.get('user_id', type=int)
        vehicle_number = request.args.get('vehicle_number')
        gate_type = request.args.get('gate_type')  # 'entry' or 'exit'
        
        # Build query
        query = '''
            SELECT 
                gs.id,
                gs.booking_id,
                gs.gate_type,
                gs.vehicle_number,
                gs.scan_time,
                gs.success,
                gs.overstay,
                gs.additional_charge,
                gs.total_cost,
                gs.message,
                gs.user_id,
                u.username
            FROM gate_scans gs
            LEFT JOIN users u ON gs.user_id = u.id
            WHERE 1=1
        '''
        params = []
        
        if user_id:
            query += ' AND gs.user_id = ?'
            params.append(user_id)
        
        if vehicle_number:
            query += ' AND gs.vehicle_number LIKE ?'
            params.append(f'%{vehicle_number}%')
        
        if gate_type:
            query += ' AND gs.gate_type = ?'
            params.append(gate_type)
        
        query += ' ORDER BY gs.scan_time DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        scans = cursor.fetchall()
        
        history = []
        for scan in scans:
            history.append({
                'id': scan[0],
                'booking_id': scan[1],
                'gate_type': scan[2],
                'vehicle_number': scan[3],
                'scan_time': scan[4],
                'success': bool(scan[5]),
                'overstay': bool(scan[6]) if scan[6] else False,
                'additional_charge': scan[7] if scan[7] else 0,
                'total_cost': scan[8] if scan[8] else 0,
                'message': scan[9],
                'user_id': scan[10],
                'username': scan[11] if scan[11] else 'N/A'
            })
        
        return jsonify({
            'success': True,
            'count': len(history),
            'scan_history': history
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        conn.close()


@app.route('/api/user-scan-history', methods=['GET'])
def get_user_scan_history():
    """Get scan history for logged-in user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        user_id = session['user_id']
        
        cursor.execute('''
            SELECT 
                gs.id,
                gs.booking_id,
                gs.gate_type,
                gs.vehicle_number,
                gs.scan_time,
                gs.success,
                gs.overstay,
                gs.additional_charge,
                gs.total_cost,
                gs.message
            FROM gate_scans gs
            WHERE gs.user_id = ?
            ORDER BY gs.scan_time DESC
            LIMIT 100
        ''', (user_id,))
        
        scans = cursor.fetchall()
        
        history = []
        for scan in scans:
            history.append({
                'id': scan[0],
                'booking_id': scan[1],
                'gate_type': scan[2],
                'vehicle_number': scan[3],
                'scan_time': scan[4],
                'success': bool(scan[5]),
                'overstay': bool(scan[6]) if scan[6] else False,
                'additional_charge': scan[7] if scan[7] else 0,
                'total_cost': scan[8] if scan[8] else 0,
                'message': scan[9]
            })
        
        return jsonify({
            'success': True,
            'count': len(history),
            'scan_history': history
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    finally:
        conn.close()


# Serve frontend


@app.route('/')
def serve_frontend():
    return send_from_directory('../frontend', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)


# Initialize database on module load
os.makedirs('backend/database', exist_ok=True)
init_db()

if __name__ == '__main__':
    # Create database directory if it doesn't exist
    os.makedirs('backend/database', exist_ok=True)

    # Initialize database
    init_db()

    print("🚀 University Parking System Starting...")
    print("📊 Database initialized")
    print("🌐 Server running at: http://localhost:5000")
    print("💡 Press Ctrl+C to stop the server")

    # Run Flask app
    # Use 0.0.0.0 to allow external connections (mobile, network access)
    # In production, debug should be False
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', debug=True, port=port)
