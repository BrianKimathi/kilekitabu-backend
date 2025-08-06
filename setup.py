#!/usr/bin/env python3
"""
Setup script for KileKitabu Backend
This script helps configure and start the backend server
"""

import os
import subprocess
import sys

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        import flask
        import firebase_admin
        import requests
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_firebase_config():
    """Check if Firebase configuration is available"""
    print("🔍 Checking Firebase configuration...")
    
    firebase_file = "kile-kitabu-firebase-adminsdk-pjk21-d2e073c9ae.json"
    if os.path.exists(firebase_file):
        print(f"✅ Firebase service account file found: {firebase_file}")
        return True
    else:
        print(f"❌ Firebase service account file not found: {firebase_file}")
        return False

def create_env_file():
    """Create .env file with current configuration"""
    print("🔧 Creating .env file...")
    
    env_content = """# Flask Configuration
SECRET_KEY=kilekitabu-secret-key-2024-change-in-production
FLASK_DEBUG=True
HOST=0.0.0.0
PORT=5000

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=kile-kitabu-firebase-adminsdk-pjk21-d2e073c9ae.json
FIREBASE_DATABASE_URL=https://kile-kitabu-default-rtdb.firebaseio.com



# PesaPal Configuration
PESAPAL_CONSUMER_KEY=sRE8q61NY+L2TophDXPUsfF/fLZ+Wz7Z
PESAPAL_CONSUMER_SECRET=VgLnSaRRXpuZsH69EMRH62uFmdk=
PESAPAL_BASE_URL=https://www.pesapal.com

# App Configuration
BASE_URL=http://localhost:5000
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def start_server():
    """Start the Flask server"""
    print("🚀 Starting KileKitabu Backend server...")
    
    try:
        # Start the Flask app
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main setup function"""
    print("🎯 KileKitabu Backend Setup")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check Firebase config
    if not check_firebase_config():
        return
    
    # Create .env file
    if not create_env_file():
        return
    
    print("\n✅ Setup completed successfully!")
    print("\n📋 Configuration Summary:")
    print("- Firebase: ✅ Configured")
    print("- PesaPal: ✅ Credentials ready")h
    print("- Environment: ✅ .env file created")
    
    print("\n🚀 Ready to start server!")
    print("Press Ctrl+C to stop the server")
    print("=" * 40)
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()