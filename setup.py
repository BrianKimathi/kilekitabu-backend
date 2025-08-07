#!/usr/bin/env python3
"""
Setup script for Pesapal integration
This script helps configure and test the Pesapal integration
"""

import os
import sys
import shutil

def create_env_file():
    """Create .env file from template"""
    env_template = """# Pesapal Configuration
PESAPAL_CONSUMER_KEY=your_consumer_key_here
PESAPAL_CONSUMER_SECRET=your_consumer_secret_here
PESAPAL_ENVIRONMENT=sandbox  # 'sandbox' or 'production'

# Application Configuration
BASE_URL=http://localhost:5000
FRONTEND_URL=http://localhost:3000

# Database Configuration
DATABASE_URL=sqlite:///kilekitabu.db

# Security Configuration
SECRET_KEY=your-secret-key-here

# Logging Configuration
LOG_LEVEL=INFO

# Flask Configuration
FLASK_DEBUG=True
HOST=0.0.0.0
PORT=5000
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_template)
        print("✓ Created .env file")
        print("⚠️  Please update .env file with your actual Pesapal credentials")
    else:
        print("✓ .env file already exists")

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ['flask', 'requests', 'python-dotenv']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"✗ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("✓ All required packages are installed")
        return True

def check_files():
    """Check if all required files exist"""
    required_files = [
        'config.py',
        'pesapal_integration_v2.py',
        'payment_api.py',
        'app.py',
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"✗ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("✓ All required files exist")
        return True

def test_imports():
    """Test if all imports work correctly"""
    try:
        from config import Config
        print("✓ Config imported successfully")
    except Exception as e:
        print(f"✗ Config import failed: {e}")
        return False
    
    try:
        from pesapal_integration_v2 import PesaPalIntegration
        print("✓ PesaPalIntegration imported successfully")
    except Exception as e:
        print(f"✗ PesaPalIntegration import failed: {e}")
        return False
    
    try:
        from payment_api import app
        print("✓ Payment API imported successfully")
    except Exception as e:
        print(f"✗ Payment API import failed: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("Pesapal Integration Setup")
    print("=" * 40)
    
    # Check files
    if not check_files():
        print("\nSetup failed: Missing required files")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\nSetup failed: Missing dependencies")
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Test imports
    if not test_imports():
        print("\nSetup failed: Import errors")
        sys.exit(1)
    
    print("\n" + "=" * 40)
    print("✓ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update .env file with your Pesapal credentials")
    print("2. Run: python test_pesapal_integration.py")
    print("3. Run: python app.py")
    print("\nFor testing:")
    print("- Use sandbox credentials first")
    print("- Test with small amounts")
    print("- Monitor logs for any errors")

if __name__ == "__main__":
    main()