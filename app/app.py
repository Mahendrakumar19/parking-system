from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime, timedelta
import qrcode
import io
import base64
import json
import uuid
import os
from database import Database

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Initialize database
db = Database()

# Pricing configuration
PRICING = {
    'bike': 20,  # ₹20 per hour
    'car': 30    # ₹30 per hour
}

FINE_MULTIPLIER = 2  # Fine is 2x the hourly rate

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_data = {
            'name': request.form['name'],
            'mobile': request.form['mobile'],
            'address': request.form['address'],
            'department': request.form['department'],
            'university_id': request.form['university_id'],
            'email': request.form['email']
        }
        
        try:
            user_id = db.create_user(user_data)
            return render_template('registration_success.html', user_id=user_id)
        except Exception as e:
            return render_template('register.html', error='Registration failed. Please try again.')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        user = db.get_user_by_id(user_id)
        
        if user:
            session['user_id'] = user_id
            session['user_name'] = user[2]  # name is at index 2
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid User ID')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    bookings = db.get_user_bookings(user_id)
    pending_fines = db.get_pending_fines(user_id)
    
    # Find active booking
    active_booking = None
    for booking in bookings:
        if booking[10] == 'active':  # status is at index 10
            active_booking = booking
            break
    
    return render_template('dashboard.html', 
                         user_name=session['user_name'],
                         active_booking=active_booking,
                         pending_fines=pending_fines,
                         bookings=bookings[:5])  # Show last 5 bookings

@app.route('/book', methods=['GET', 'POST'])
def book():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        vehicle_type = request.form['vehicle_type']
        vehicle_number = request.form['vehicle_number']
        entry_time = datetime.strptime(request.form['entry_time'], '%Y-%m-%dT%H:%M')
        exit_time = datetime.strptime(request.form['exit_time'], '%Y-%m-%dT%H:%M')
        
        # Check if exit time is after entry time
        if exit_time <= entry_time:
            return render_template('book.html', error='Exit time must be after entry time')
        
        # Calculate duration and amount
        duration = (exit_time - entry_time).total_seconds() / 3600  # hours
        parking_amount = duration * PRICING[vehicle_type]
        
        # Check pending fines
        pending_fines = db.get_pending_fines(session['user_id'])
        total_amount = parking_amount + pending_fines
        
        # Check slot availability
        available_slots = db.check_slot_availability(vehicle_type, entry_time, exit_time)
        
        if available_slots <= 0:
            return render_template('book.html', 
                                 error='No slots available for the selected time period')
        
        # Find and reserve a specific parking spot
        available_spot = db.find_available_spot(vehicle_type, entry_time, exit_time)
        
        if not available_spot:
            return render_template('book.html', 
                                 error='No specific parking spots available for the selected time period')
        
        spot_number, zone, floor_level = available_spot
        
        # Generate QR code
        booking_id = str(uuid.uuid4())[:12].upper()
        booking_data = {
            'booking_id': booking_id,
            'user_id': session['user_id'],
            'vehicle_type': vehicle_type,
            'vehicle_number': vehicle_number,
            'entry_time': entry_time.isoformat(),
            'exit_time': exit_time.isoformat()
        }
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(json.dumps(booking_data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()
        
        # Create booking
        booking_info = {
            'booking_id': booking_id,
            'user_id': session['user_id'],
            'vehicle_number': vehicle_number,
            'vehicle_type': vehicle_type,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'amount': parking_amount,
            'qr_code': qr_code_data
        }
        
        booking_id = db.create_booking(booking_info)
        
        # Reserve the specific parking spot
        db.reserve_parking_spot(booking_id, spot_number, entry_time, exit_time)
        
        # Create transaction record
        transaction_data = {
            'user_id': session['user_id'],
            'booking_id': booking_id,
            'transaction_type': 'booking',
            'parking_amount': parking_amount,
            'fine_amount': pending_fines,
            'total_amount': total_amount,
            'description': f'Parking booking for {vehicle_type} {vehicle_number} - {duration:.1f} hours - Spot {spot_number}'
        }
        transaction_id = db.create_transaction(transaction_data)
        
        # Pay any pending fines
        if pending_fines > 0:
            db.pay_pending_fines(session['user_id'])
        
        return render_template('booking_success.html',
                             booking_id=booking_id,
                             transaction_id=transaction_id,
                             vehicle_type=vehicle_type,
                             vehicle_number=vehicle_number,
                             duration=duration,
                             parking_amount=parking_amount,
                             pending_fines=pending_fines,
                             total_amount=total_amount,
                             qr_code=qr_code_data,
                             available_slots=available_slots,
                             spot_number=spot_number,
                             zone=zone,
                             floor_level=floor_level,
                             entry_time=entry_time.strftime('%d %b %Y, %I:%M %p'),
                             exit_time=exit_time.strftime('%d %b %Y, %I:%M %p'))
    
    return render_template('book.html')

@app.route('/check_availability')
def check_availability():
    vehicle_type = request.args.get('vehicle_type')
    entry_time = datetime.fromisoformat(request.args.get('entry_time'))
    exit_time = datetime.fromisoformat(request.args.get('exit_time'))
    
    available_slots = db.check_slot_availability(vehicle_type, entry_time, exit_time)
    
    return jsonify({'available_slots': available_slots})

@app.route('/scan_entry', methods=['POST'])
def scan_entry():
    try:
        qr_data = json.loads(request.json['qr_data'])
        booking_id = qr_data.get('booking_id')
        booking = db.get_booking_by_id(booking_id)
        
        if booking:
            # Update entry time
            db.update_entry_time(booking_id, datetime.now())
            
            # Get assigned parking spot
            spot = db.get_parking_spot_by_booking(booking_id)
            
            if spot:
                spot_number = spot[0]
                zone = spot[1]
                # Mark spot as occupied
                db.occupy_parking_spot(booking_id, spot_number)
                
                return jsonify({
                    'success': True, 
                    'message': f'Entry recorded successfully. Your assigned parking spot is {spot_number} in Zone {zone}.',
                    'spot_number': spot_number,
                    'zone': zone
                })
            else:
                return jsonify({'success': True, 'message': 'Entry recorded successfully'})
        else:
            return jsonify({'success': False, 'message': 'Invalid QR code'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error processing entry'})

@app.route('/scan_exit', methods=['POST'])
def scan_exit():
    try:
        qr_data = json.loads(request.json['qr_data'])
        booking_id = qr_data.get('booking_id')
        booking = db.get_booking_by_id(booking_id)
        
        if booking:
            current_time = datetime.now()
            # Check if user is exiting late
            scheduled_exit = datetime.fromisoformat(booking[6])  # exit_time is at index 6
            
            # Get assigned parking spot
            spot = db.get_parking_spot_by_booking(booking_id)
            spot_number = spot[0] if spot else None
            
            fine_amount = 0
            if current_time > scheduled_exit:
                # Add fine for late exit
                fine_amount = PRICING[booking[4]] * FINE_MULTIPLIER  # vehicle_type is at index 4
                db.add_fine(booking[2], booking[1], fine_amount, 'Late exit')  # user_id, booking_id
                
                # Create transaction record for fine
                fine_transaction_data = {
                    'user_id': booking[2],
                    'booking_id': booking[1],
                    'transaction_type': 'fine',
                    'fine_amount': fine_amount,
                    'total_amount': fine_amount,
                    'description': f'Late exit fine for {booking[4]} {booking[3]} - exceeded time by {int((current_time - scheduled_exit).total_seconds() / 60)} minutes'
                }
                db.create_transaction(fine_transaction_data)
            
            # Update exit time
            db.update_exit_time(booking[1], current_time)
            
            # Free up the parking spot
            if spot_number:
                db.free_parking_spot(booking_id, spot_number)
            
            response_message = f'Exit recorded successfully'
            if spot_number:
                response_message += f'. Parking spot {spot_number} is now available'
            if fine_amount > 0:
                response_message += f'. Late exit fine of ₹{fine_amount} has been added to your account'
            
            return jsonify({
                'success': True, 
                'message': response_message,
                'fine_amount': fine_amount,
                'spot_freed': spot_number
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid QR code'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error processing exit'})

@app.route('/extend_booking/<booking_id>', methods=['POST'])
def extend_booking(booking_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    try:
        additional_hours = int(request.json['hours'])
        booking = db.get_booking_by_id(booking_id)
        
        if not booking or booking[2] != session['user_id']:  # user_id is at index 2
            return jsonify({'success': False, 'message': 'Booking not found'})
        
        # Check if booking is still active or booked
        if booking[10] not in ['booked', 'active']:  # status is at index 10
            return jsonify({'success': False, 'message': 'Cannot extend completed booking'})
        
        # Calculate new exit time and additional cost
        current_exit = datetime.fromisoformat(booking[6])  # exit_time is at index 6
        new_exit = current_exit + timedelta(hours=additional_hours)
        additional_cost = additional_hours * PRICING[booking[4]]  # vehicle_type is at index 4
        
        # Check slot availability for extended period
        available_slots = db.check_slot_availability(booking[4], current_exit, new_exit)
        
        if available_slots <= 0:
            return jsonify({'success': False, 'message': 'No slots available for extension'})
        
        # Update booking in database
        db.extend_booking_time(booking_id, new_exit, additional_cost)
        
        # Extend spot reservation
        db.extend_spot_reservation(booking_id, new_exit)
        
        # Create transaction record for extension
        transaction_data = {
            'user_id': session['user_id'],
            'booking_id': booking_id,
            'transaction_type': 'extension',
            'extension_amount': additional_cost,
            'total_amount': additional_cost,
            'description': f'Booking extension for {additional_hours} hour(s) - {booking[4]} {booking[3]}'
        }
        extension_transaction_id = db.create_transaction(transaction_data)
        
        return jsonify({
            'success': True, 
            'additional_cost': additional_cost,
            'transaction_id': extension_transaction_id,
            'new_exit_time': new_exit.strftime('%Y-%m-%d %H:%M'),
            'message': f'Booking extended by {additional_hours} hour(s)'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error extending booking'})

@app.route('/live_slots')
def live_slots():
    """Real-time parking slots monitoring page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get live parking status
    bike_status = db.get_live_parking_status('bike')
    car_status = db.get_live_parking_status('car')
    
    # Get all spots with detailed status
    bike_spots = db.get_all_spots_with_status('bike')
    car_spots = db.get_all_spots_with_status('car')
    
    return render_template('live_slots.html',
                         bike_status=bike_status,
                         car_status=car_status,
                         bike_spots=bike_spots,
                         car_spots=car_spots)

@app.route('/api/live_status')
def api_live_status():
    """API endpoint for real-time status updates"""
    vehicle_type = request.args.get('type')
    
    if vehicle_type:
        status = db.get_live_parking_status(vehicle_type)
        spots = db.get_all_spots_with_status(vehicle_type)
    else:
        status = db.get_live_parking_status()
        spots = db.get_all_spots_with_status()
    
    return jsonify({
        'status': status,
        'spots': spots,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/my_spot')
def my_spot():
    """Show user's current parking spot"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    bookings = db.get_user_bookings(user_id)
    
    # Find active booking
    active_booking = None
    assigned_spot = None
    
    for booking in bookings:
        if booking[10] == 'active':  # status is at index 10
            active_booking = booking
            assigned_spot = db.get_parking_spot_by_booking(booking[1])  # booking_id
            break
    
    return render_template('my_spot.html',
                         active_booking=active_booking,
                         assigned_spot=assigned_spot)

@app.route('/transaction/<transaction_id>')
def transaction_details(transaction_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    transaction = db.get_transaction_by_id(transaction_id)
    
    if not transaction or transaction[1] != session['user_id']:  # user_id is at index 1
        return redirect(url_for('transactions'))
    
    # Get related booking if exists
    booking = None
    if transaction[2]:  # booking_id is at index 2
        booking = db.get_booking_by_id(transaction[2])
    
    return render_template('transaction_details.html',
                         transaction=transaction,
                         booking=booking)

@app.route('/transactions')
def transactions():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    transactions = db.get_user_transactions(user_id, 20)  # Get last 20 transactions
    pending_fines = db.get_pending_fines(user_id)
    
    # Calculate total spent and transaction count
    total_spent = sum(t[7] for t in transactions)  # total_amount is at index 7
    transaction_count = len(transactions)
    
    return render_template('transactions.html',
                         transactions=transactions,
                         total_spent=total_spent,
                         transaction_count=transaction_count,
                         pending_fines=pending_fines)

@app.route('/scanner')
def scanner():
    return render_template('scanner.html')

# Admin routes for QR verification
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = db.authenticate_admin(username, password)
        if admin:
            session['admin_id'] = admin['admin_id']
            session['admin_name'] = admin['name']
            session['admin_role'] = admin['role']
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    # Get recent entry/exit logs
    recent_logs = db.get_entry_exit_logs(limit=50)
    
    # Get today's statistics
    from datetime import datetime, timedelta
    today = datetime.now().date()
    
    # Count today's entries and exits
    entry_count = sum(1 for log in recent_logs if log['action_type'] == 'entry' and 
                     datetime.fromisoformat(log['timestamp']).date() == today)
    exit_count = sum(1 for log in recent_logs if log['action_type'] == 'exit' and 
                    datetime.fromisoformat(log['timestamp']).date() == today)
    
    return render_template('admin_dashboard.html',
                         admin_name=session['admin_name'],
                         admin_role=session['admin_role'],
                         recent_logs=recent_logs,
                         entry_count=entry_count,
                         exit_count=exit_count)

@app.route('/admin/scanner')
def admin_scanner():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_scanner.html',
                         admin_name=session['admin_name'])

@app.route('/admin/verify_qr', methods=['POST'])
def verify_qr():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        qr_data = request.json.get('qr_data')
        action_type = request.json.get('action_type', 'entry')  # 'entry' or 'exit'
        
        # Parse QR code data
        import json as json_module
        booking_data = json_module.loads(qr_data)
        booking_id = booking_data.get('booking_id')
        
        if not booking_id:
            return jsonify({'success': False, 'message': 'Invalid QR code format'})
        
        # Verify booking exists
        booking_info = db.verify_qr_booking(booking_id)
        if not booking_info:
            return jsonify({'success': False, 'message': 'Invalid or expired booking'})
        
        # Check for duplicate entry/exit
        if db.check_duplicate_entry_exit(booking_id, action_type):
            return jsonify({'success': False, 'message': f'{action_type.title()} already recorded for this booking'})
        
        # Validate timing
        from datetime import datetime
        current_time = datetime.now()
        entry_time = datetime.fromisoformat(booking_info['entry_time'])
        exit_time = datetime.fromisoformat(booking_info['exit_time'])
        
        if action_type == 'entry':
            # Allow entry 15 minutes before scheduled time
            if current_time < entry_time - timedelta(minutes=15):
                return jsonify({'success': False, 'message': 'Too early for entry'})
        elif action_type == 'exit':
            # Must have entered first
            if not db.check_duplicate_entry_exit(booking_id, 'entry'):
                return jsonify({'success': False, 'message': 'Must enter before exit'})
        
        # Record the entry/exit
        success = db.record_entry_exit(booking_id, action_type, session['admin_id'], booking_info['spot_number'])
        
        if success:
            return jsonify({
                'success': True,
                'message': f'{action_type.title()} verified successfully',
                'booking_info': {
                    'booking_id': booking_info['booking_id'],
                    'user_name': booking_info['user_name'],
                    'vehicle_number': booking_info['vehicle_number'],
                    'vehicle_type': booking_info['vehicle_type'],
                    'spot_number': booking_info['spot_number'],
                    'zone': booking_info['zone'],
                    'entry_time': booking_info['entry_time'],
                    'exit_time': booking_info['exit_time']
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to record entry/exit'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing QR code: {str(e)}'})

@app.route('/admin/logs')
def admin_logs():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    # Get all logs with pagination
    page = request.args.get('page', 1, type=int)
    limit = 100
    
    logs = db.get_entry_exit_logs(limit=limit)
    
    return render_template('admin_logs.html',
                         logs=logs,
                         admin_name=session['admin_name'])

@app.route('/admin/logout')
def admin_logout():
    # Clear only admin session data
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    session.pop('admin_role', None)
    session.pop('is_admin', None)
    return redirect(url_for('admin_login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)