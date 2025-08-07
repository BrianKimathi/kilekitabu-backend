#!/usr/bin/env python3
"""
Test script for Pesapal integration
Run this script to test the Pesapal API integration
"""

import os
import sys
import json
from pesapal_integration_v2 import PesaPalIntegration
from config import Config

def test_pesapal_integration():
    """Test the Pesapal integration"""
    print("Testing Pesapal Integration...")
    print("=" * 50)
    
    # Initialize Pesapal integration
    try:
        pesapal = PesaPalIntegration()
        print("✓ Pesapal integration initialized")
    except Exception as e:
        print(f"✗ Failed to initialize Pesapal integration: {e}")
        return False
    
    # Test access token
    print("\n1. Testing access token...")
    try:
        token = pesapal._get_access_token()
        if token:
            print("✓ Access token obtained successfully")
        else:
            print("✗ Failed to get access token")
            return False
    except Exception as e:
        print(f"✗ Error getting access token: {e}")
        return False
    
    # Test IPN registration
    print("\n2. Testing IPN registration...")
    try:
        ipn_url = f"{Config.BASE_URL}/api/payment/ipn"
        ipn_id = pesapal.register_ipn_url(ipn_url)
        if ipn_id:
            print(f"✓ IPN registered successfully with ID: {ipn_id}")
        else:
            print("✗ Failed to register IPN")
            return False
    except Exception as e:
        print(f"✗ Error registering IPN: {e}")
        return False
    
    # Test payment creation
    print("\n3. Testing payment creation...")
    try:
        payment_data = {
            'payment_id': 'TEST_123456',
            'amount': 100.0,
            'credit_days': 30,
            'email': 'test@example.com',
            'phone': '+254712345678',
            'first_name': 'Test',
            'last_name': 'User',
            'address': '123 Test St',
            'city': 'Nairobi',
            'state': 'NBI',
            'postal_code': '00100',
            'is_subscription': False
        }
        
        result = pesapal.create_payment_request(payment_data)
        if result and result.get('payment_url'):
            print("✓ Payment request created successfully")
            print(f"  Payment URL: {result['payment_url']}")
            print(f"  Order Tracking ID: {result['order_tracking_id']}")
        else:
            print("✗ Failed to create payment request")
            return False
    except Exception as e:
        print(f"✗ Error creating payment request: {e}")
        return False
    
    # Test payment status check (with dummy ID)
    print("\n4. Testing payment status check...")
    try:
        # This will likely fail with a dummy ID, but we're testing the API call
        dummy_tracking_id = "dummy-tracking-id-123"
        result = pesapal.check_payment_status(dummy_tracking_id)
        if result is not None:
            print("✓ Payment status check API call successful")
        else:
            print("✗ Payment status check failed")
            return False
    except Exception as e:
        print(f"✗ Error checking payment status: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ All tests completed successfully!")
    print("The Pesapal integration is working correctly.")
    return True

def test_configuration():
    """Test the configuration"""
    print("Testing Configuration...")
    print("=" * 30)
    
    try:
        # Test configuration validation
        Config.validate_config()
        print("✓ Configuration validation passed")
    except ValueError as e:
        print(f"✗ Configuration validation failed: {e}")
        print("Please check your .env file and ensure all required variables are set.")
        return False
    
    # Print configuration summary
    print(f"\nConfiguration Summary:")
    print(f"  Environment: {Config.PESAPAL_ENVIRONMENT}")
    print(f"  Base URL: {Config.PESAPAL_BASE_URL}")
    print(f"  Consumer Key: {Config.PESAPAL_CONSUMER_KEY[:10]}...")
    print(f"  Consumer Secret: {Config.PESAPAL_CONSUMER_SECRET[:10]}...")
    
    return True

def main():
    """Main test function"""
    print("Pesapal Integration Test")
    print("=" * 50)
    
    # Test configuration first
    if not test_configuration():
        print("\nConfiguration test failed. Please fix the configuration and try again.")
        sys.exit(1)
    
    # Test integration
    if not test_pesapal_integration():
        print("\nIntegration test failed. Please check the error messages above.")
        sys.exit(1)
    
    print("\n🎉 All tests passed! Your Pesapal integration is ready to use.")
    print("\nNext steps:")
    print("1. Update your .env file with real Pesapal credentials")
    print("2. Test with real payment amounts")
    print("3. Deploy to production when ready")

if __name__ == "__main__":
    main() 