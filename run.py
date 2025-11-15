#!/usr/bin/env python3
"""
University Parking Management System - Main Runner
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import flask
        import flask_cors
        return True
    except ImportError:
        return False

def install_dependencies():
    """Install required packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def main():
    print("🚗 University Parking Management System")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Required packages not found.")
        if input("🤔 Do you want to install them now? (y/n): ").lower() == 'y':
            if not install_dependencies():
                return
        else:
            print("💡 Please install dependencies manually:")
            print("   pip install -r backend/requirements.txt")
            return
    
    # Import and run the app
    try:
        # Add backend to Python path
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from backend.app import app
        
        print("✅ System initialized successfully!")
        print("🌐 Starting web server...")
        print("📍 Access your application at: http://localhost:5000")
        print("⏹️  Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Run Flask app
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f"❌ Error importing application: {e}")
        print("💡 Make sure all files are in the correct locations")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == '__main__':
    main()