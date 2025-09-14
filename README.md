# University Parking Management System

A comprehensive web-based parking management system built with Python Flask for university campuses. This system handles vehicle registration, slot booking, QR code-based entry/exit, and automated fine management.

## 🚀 Features

### User Management
- **Student Registration**: Complete user registration with university details
- **Unique User ID**: Auto-generated unique identifiers for each user
- **Simple Login**: Secure login using User ID

### Vehicle Booking System
- **Multi-Vehicle Support**: Separate pricing for bikes (₹20/hour) and cars (₹30/hour)
- **Real-time Availability**: Live slot availability checking
- **Flexible Scheduling**: Choose custom entry and exit times
- **QR Code Generation**: Automatic QR code creation for each booking
- **Fine Integration**: Automatically includes pending fines in payment

### Smart Entry/Exit System
- **QR Code Scanning**: Entry and exit via QR code scanning
- **Automatic Logging**: Real-time entry/exit time recording
- **Late Exit Detection**: Automatic fine calculation for overdue exits
- **Gate Simulation**: Built-in scanner simulation for testing

### Booking Management
- **Dashboard Overview**: Complete booking history and status
- **Active Booking Tracking**: Real-time status of current bookings
- **Booking Extension**: Extend parking time if slots available
- **Multiple Actions**: Extend or view QR codes from recent bookings table

### Recent Bookings Table Actions
- **Extend Button**: Available for active and booked slots
- **QR Code Button**: View/print QR code for active bookings
- **Status-based Actions**: Different options based on booking status
- **Real-time Updates**: Actions update based on current booking state

### Fine Management System
- **Automatic Fines**: 2x hourly rate for late exits
- **Fine Tracking**: Comprehensive fine history and status
- **Payment Integration**: Mandatory fine payment with next booking
- **Transparent Billing**: Clear breakdown of charges and fines

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **QR Code**: qrcode library
- **Image Processing**: Pillow

## Project Structure

```
university_parking/
├── app/
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── register.html
│   │   ├── registration_success.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── book.html
│   │   ├── booking_success.html
│   │   └── scanner.html
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       ├── booking.js
│   │       └── dashboard.js
│   ├── app.py
│   └── database.py
├── requirements.txt
└── README.md
```

## Installation and Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Step 1: Clone/Download the Project
If you have this project as a ZIP file, extract it to your desired location.

### Step 2: Install Dependencies
Open a terminal/command prompt in the project directory and run:

```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
Navigate to the app directory and run:

```bash
cd app
python app.py
```

The application will start on `http://localhost:5000`

## Usage Guide

### For New Users

1. **Visit the Portal**: Go to `http://localhost:5000`
2. **Register**: Click "New User Registration"
3. **Fill Details**: Enter your name, mobile, address, department, university ID, and email
4. **Save User ID**: After registration, save your unique User ID

### For Returning Users

1. **Login**: Click "Already Registered" and enter your User ID
2. **Dashboard**: View your current bookings and pending fines

### Booking a Parking Slot

1. **Select Vehicle**: Choose Bike (₹20/hour) or Car (₹30/hour)
2. **Enter Details**: Vehicle number, entry time, and exit time
3. **Check Availability**: System shows available slots
4. **Confirm Booking**: Make payment and receive QR code
5. **Save QR Code**: Print or save the QR code for entry/exit

### Using the Parking

1. **Entry**: Scan QR code at entry gate
2. **Park**: Park in any available slot of your vehicle type
3. **Reminder**: Receive reminder 15 minutes before exit time
4. **Extend** (if needed): Login to extend booking if slots available
5. **Exit**: Scan QR code at exit gate

### Testing the Scanner

Visit `http://localhost:5000/scanner` to test the QR code scanning functionality.

## Database Schema

### Users Table
- id, user_id, name, mobile, address, department, university_id, email, created_at

### Bookings Table
- id, booking_id, user_id, vehicle_number, vehicle_type, entry_time, exit_time, actual_entry_time, actual_exit_time, amount, status, qr_code, created_at

### Fines Table
- id, user_id, booking_id, amount, reason, status, created_at

### Parking Slots Table
- id, slot_type, total_slots, occupied_slots

## Configuration

### Parking Capacity
- Bikes: 50 slots
- Cars: 30 slots

### Pricing
- Bikes: ₹20 per hour
- Cars: ₹30 per hour

### Fines
- Late exit: 2x hourly rate (₹40 for bikes, ₹60 for cars)

## Development Notes

### Security Considerations
- Use proper session management for production
- Implement proper authentication and authorization
- Add input validation and sanitization
- Use environment variables for sensitive configuration

### Potential Enhancements
- SMS/Email notifications
- Payment gateway integration
- Mobile app development
- Real-time slot monitoring with IoT sensors
- Admin dashboard for parking management
- Reporting and analytics
- Multi-campus support

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Error**: Delete `parking.db` file and restart the application to recreate

3. **Port Already in Use**: Change the port in app.py:
   ```python
   app.run(debug=True, port=5001)
   ```

4. **QR Code Not Generating**: Ensure Pillow is installed correctly

## License

This project is for educational purposes. Feel free to use and modify as needed.

## Support

For issues or questions, please check the troubleshooting section or review the code comments for implementation details.