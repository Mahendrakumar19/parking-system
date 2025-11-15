
import qrcode
import io
import base64
import json
import hashlib
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont


class QRCodeSystem:
    """Handles QR code generation and validation for parking system"""
    
    def __init__(self):
        self.secret_key = "PARKING_SYSTEM_SECRET_2025"
    
    def generate_qr_code(self, booking_id, user_id, vehicle_number, vehicle_type, 
                         entry_time, exit_time, slot_number):
        """
        Generate a secure QR code for parking entry/exit
        Similar to metro card QR codes
        """
        # Create QR data with encrypted information
        qr_data = {
            'booking_id': booking_id,
            'user_id': user_id,
            'vehicle_number': vehicle_number,
            'vehicle_type': vehicle_type,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'slot_number': slot_number,
            'timestamp': datetime.now().isoformat(),
            'checksum': self._generate_checksum(booking_id, user_id, vehicle_number)
        }
        
        # Convert to JSON string
        qr_string = json.dumps(qr_data)
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)
        
        # Create image with custom styling (metro-style)
        img = qr.make_image(fill_color="#1a1a2e", back_color="white")
        
        # Convert to base64 for easy storage and transmission
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            'qr_code_image': f"data:image/png;base64,{img_str}",
            'qr_data': qr_data,
            'qr_string': qr_string
        }
    
    def _generate_checksum(self, booking_id, user_id, vehicle_number):
        """Generate a secure checksum for QR validation"""
        data = f"{booking_id}{user_id}{vehicle_number}{self.secret_key}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def validate_qr_code(self, qr_string):
        """
        Validate QR code data
        Returns: dict with 'valid', 'booking_id', 'qr_data', 'message'
        """
        try:
            qr_data = json.loads(qr_string)
            
            # Verify checksum
            expected_checksum = self._generate_checksum(
                qr_data['booking_id'],
                qr_data['user_id'],
                qr_data['vehicle_number']
            )
            
            if qr_data['checksum'] != expected_checksum:
                return {
                    'valid': False,
                    'booking_id': None,
                    'qr_data': None,
                    'message': "Invalid QR code - checksum mismatch"
                }
            
            return {
                'valid': True,
                'booking_id': qr_data['booking_id'],
                'qr_data': qr_data,
                'message': 'Valid QR code'
            }
            
        except json.JSONDecodeError:
            return {
                'valid': False,
                'booking_id': None,
                'qr_data': None,
                'message': "Invalid QR code format"
            }
        except KeyError as e:
            return {
                'valid': False,
                'booking_id': None,
                'qr_data': None,
                'message': f"Missing required field: {str(e)}"
            }
    
    def verify_entry(self, qr_data, current_time=None):
        """
        Verify if QR code can be used for entry
        Similar to metro gate entry validation
        """
        if current_time is None:
            current_time = datetime.now()
        
        entry_time = datetime.fromisoformat(qr_data['entry_time'])
        exit_time = datetime.fromisoformat(qr_data['exit_time'])
        
        # Check if current time is within booking window
        if current_time < entry_time:
            return False, "Booking not yet active"
        
        if current_time > exit_time:
            return False, "Booking expired"
        
        return True, "Entry authorized"
    
    def verify_exit(self, qr_data, actual_exit_time=None):
        """
        Verify if QR code can be used for exit
        Calculate any additional charges if overstaying
        """
        if actual_exit_time is None:
            actual_exit_time = datetime.now()
        
        entry_time = datetime.fromisoformat(qr_data['entry_time'])
        exit_time = datetime.fromisoformat(qr_data['exit_time'])
        
        # Calculate if there's overstay
        if actual_exit_time > exit_time:
            overstay_hours = (actual_exit_time - exit_time).total_seconds() / 3600
            rate = 20 if qr_data['vehicle_type'] == 'bike' else 30
            additional_charge = overstay_hours * rate
            
            return True, {
                'exit_authorized': True,
                'overstay': True,
                'overstay_hours': round(overstay_hours, 2),
                'additional_charge': round(additional_charge, 2),
                'message': f"Overstay detected: {round(overstay_hours, 2)} hours extra"
            }
        
        return True, {
            'exit_authorized': True,
            'overstay': False,
            'additional_charge': 0,
            'message': "Exit authorized - on time"
        }


class DeviceScanner:
    """
    Simulates a physical QR scanner device at entry/exit gates
    Similar to metro turnstile scanners
    """
    
    def __init__(self, device_id, location, device_type='entry'):
        self.device_id = device_id
        self.location = location
        self.device_type = device_type  # 'entry' or 'exit'
        self.qr_system = QRCodeSystem()
        self.scan_history = []
    
    def scan_qr(self, qr_string):
        """
        Simulate scanning QR code at device
        Returns scan result with gate action
        """
        scan_time = datetime.now()
        
        # Validate QR code
        validation_result = self.qr_system.validate_qr_code(qr_string)
        
        if not validation_result['valid']:
            result = {
                'success': False,
                'device_id': self.device_id,
                'location': self.location,
                'scan_time': scan_time.isoformat(),
                'action': 'DENIED',
                'message': validation_result['message'],
                'gate_status': 'CLOSED'
            }
            self._log_scan(result)
            return result
        
        qr_data = validation_result['qr_data']
        
        # Verify entry or exit based on device type
        if self.device_type == 'entry':
            authorized, message = self.qr_system.verify_entry(qr_data, scan_time)
            
            result = {
                'success': authorized,
                'device_id': self.device_id,
                'location': self.location,
                'device_type': 'ENTRY GATE',
                'scan_time': scan_time.isoformat(),
                'action': 'ENTRY ALLOWED' if authorized else 'ENTRY DENIED',
                'booking_id': qr_data['booking_id'],
                'vehicle_number': qr_data['vehicle_number'],
                'vehicle_type': qr_data['vehicle_type'].upper(),
                'slot_number': qr_data['slot_number'],
                'message': message,
                'gate_status': 'OPEN' if authorized else 'CLOSED'
            }
        
        else:  # exit device
            authorized, exit_info = self.qr_system.verify_exit(qr_data, scan_time)
            
            result = {
                'success': authorized,
                'device_id': self.device_id,
                'location': self.location,
                'device_type': 'EXIT GATE',
                'scan_time': scan_time.isoformat(),
                'action': 'EXIT ALLOWED' if authorized else 'EXIT DENIED',
                'booking_id': qr_data['booking_id'],
                'vehicle_number': qr_data['vehicle_number'],
                'vehicle_type': qr_data['vehicle_type'].upper(),
                'slot_number': qr_data['slot_number'],
                'overstay': exit_info.get('overstay', False),
                'additional_charge': exit_info.get('additional_charge', 0),
                'message': exit_info.get('message', ''),
                'gate_status': 'OPEN' if authorized else 'CLOSED'
            }
        
        self._log_scan(result)
        return result
    
    def _log_scan(self, scan_result):
        """Log scan activity"""
        self.scan_history.append(scan_result)
        
        # Keep only last 100 scans in memory
        if len(self.scan_history) > 100:
            self.scan_history = self.scan_history[-100:]
    
    def get_scan_history(self, limit=10):
        """Get recent scan history"""
        return self.scan_history[-limit:]


# Initialize global QR system
qr_system = QRCodeSystem()
