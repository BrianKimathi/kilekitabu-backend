#!/usr/bin/env python3
"""
Run script for KileKitabu Backend with Pesapal integration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_configuration():
    """Check if configuration is properly set up"""
    required_vars = [
        'PESAPAL_CONSUMER_KEY',
        'PESAPAL_CONSUMER_SECRET',
        'BASE_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your_'):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Configuration Error:")
        print(f"Missing or invalid configuration: {', '.join(missing_vars)}")
        print("\nPlease update your .env file with proper values:")
        print("1. Get your Pesapal credentials from https://cybqa.pesapal.com")
        print("2. Update PESAPAL_CONSUMER_KEY and PESAPAL_CONSUMER_SECRET")
        print("3. Set BASE_URL to your server URL")
        return False
    
    return True

def main():
    """Main function to start the server"""
    print("🚀 Starting KileKitabu Backend with Pesapal Integration")
    print("=" * 60)
    
    # Check configuration
    if not check_configuration():
        sys.exit(1)
    
    try:
        # Import and start the Flask app
        from app import app
        
        # Get configuration
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        print(f"✅ Configuration loaded successfully")
        print(f"🌐 Server will run on: http://{host}:{port}")
        print(f"🔧 Debug mode: {'Enabled' if debug else 'Disabled'}")
        print(f"💳 Pesapal Environment: {os.getenv('PESAPAL_ENVIRONMENT', 'sandbox')}")
        print("\n📋 Available endpoints:")
        print("  POST /api/payment/create - Create payment")
        print("  GET  /api/payment/status/<id> - Check payment status")
        print("  GET  /api/payment/callback - Payment callback")
        print("  POST /api/payment/ipn - IPN notifications")
        print("  GET  /api/payment/cancel - Cancel payment")
        print("  POST /api/payment/refund - Request refund")
        
        print("\n🚀 Starting server...")
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Start the Flask app
        app.run(
            host=host,
            port=port,
            debug=debug
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Please run: python setup.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 