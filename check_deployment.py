#!/usr/bin/env python3
"""
Deployment verification script for University Parking System
"""

import os
import sys

def check_deployment_readiness():
    """Check if the project is ready for deployment"""
    
    print("🔍 Checking deployment readiness...\n")
    
    checks = []
    
    # Check if required files exist
    required_files = [
        'requirements.txt',
        'render.yaml',
        'app/app.py',
        'app/database.py',
        'DEPLOYMENT.md'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            checks.append(f"✅ {file} exists")
        else:
            checks.append(f"❌ {file} missing")
    
    # Check requirements.txt content
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
            if 'gunicorn' in requirements:
                checks.append("✅ Gunicorn included in requirements")
            else:
                checks.append("❌ Gunicorn missing from requirements")
    except FileNotFoundError:
        checks.append("❌ requirements.txt not found")
    
    # Check app structure
    app_files = [
        'app/templates/index.html',
        'app/templates/admin_login.html',
        'app/templates/admin_dashboard.html',
        'app/static/css/style.css'
    ]
    
    for file in app_files:
        if os.path.exists(file):
            checks.append(f"✅ {file} exists")
        else:
            checks.append(f"⚠️  {file} missing (optional)")
    
    # Print results
    for check in checks:
        print(check)
    
    print(f"\n🎯 Deployment Status:")
    if all("✅" in check for check in checks[:5]):  # Check only required files
        print("🟢 READY FOR DEPLOYMENT!")
        print("\n📋 Next Steps:")
        print("1. Commit changes: git add . && git commit -m 'Prepare for deployment'")
        print("2. Push to GitHub: git push origin main")
        print("3. Deploy on Render.com following DEPLOYMENT.md")
        return True
    else:
        print("🟡 NEEDS ATTENTION - Some files are missing")
        return False

if __name__ == "__main__":
    check_deployment_readiness()