# 🚗 Parking Management System - Quick Guide

## 📱 QR Scanner Usage

### Access Scanner
- **URL:** `http://localhost:5000/qr-test.html`
- **Mobile:** `http://YOUR_IP:5000/qr-test.html`

### How to Use
1. Open `qr-test.html` in browser
2. Select mode: ENTRY or EXIT
3. Click "Start Camera"
4. Point camera at QR code
5. Gate opens automatically

### Features
- ✅ Entry/Exit mode toggle
- ✅ Real-time QR scanning
- ✅ Automatic gate control
- ✅ Overstay detection
- ✅ Cost calculation

---

## 🌐 Cloud Hosting (FREE)

### Render.com Setup
1. Push code to GitHub
2. Connect to render.com
3. Deploy in 1 click
4. Access globally

**See:** `FREE_HOSTING_GUIDE.md` for details

---

## 📂 Project Structure

```
frontend/
  ├── qr-test.html      ← QR Scanner (Use this!)
  ├── gate-scanner.html ← Alternative scanner
  ├── book-slot.html    ← Booking page
  ├── dashboard.html    ← Admin dashboard
  └── config.js         ← API configuration

backend/
  ├── app.py           ← Main server
  ├── qr_system.py     ← QR logic
  └── database/        ← SQLite database
```

---

## 🚀 Quick Start

```bash
# Start server
cd backend
python app.py

# Access scanner
http://localhost:5000/qr-test.html
```

---

## 🛠️ Configuration

Edit `frontend/config.js` to change API URL:
```javascript
const API_URL = 'http://localhost:5000';  // Local
// or
const API_URL = 'http://192.168.1.X:5000';  // Mobile
```

---

## 📞 Support

All features working:
- ✅ QR Generation
- ✅ QR Scanning  
- ✅ Entry/Exit tracking
- ✅ Overstay penalties
- ✅ 2-scan limit

Ready for deployment! 🎉
