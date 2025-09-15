#!/usr/bin/env python3
"""
Debug script to check config values
"""
import os
from dotenv import load_dotenv

print("=== Debug Config ===")
print("1. Loading .env file...")
load_dotenv()

print("2. Environment variables:")
print(f"   FIREBASE_CREDENTIALS_PATH: {os.getenv('FIREBASE_CREDENTIALS_PATH', 'NOT_SET')}")

print("3. Direct os.getenv test:")
result = os.getenv('FIREBASE_CREDENTIALS_PATH', 'kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json')
print(f"   Result: {result}")

print("4. Importing config...")
try:
    from config import Config
    print(f"   Config.FIREBASE_CREDENTIALS_PATH: {Config.FIREBASE_CREDENTIALS_PATH}")
except Exception as e:
    print(f"   Error importing config: {e}")

print("5. Checking if file exists:")
import os
if os.path.exists('kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json'):
    print("   ✅ File exists: kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json")
else:
    print("   ❌ File does not exist: kile-kitabu-firebase-adminsdk-pjk21-68cbd0c3b4.json")

if os.path.exists('kile-kitabu-firebase-adminsdk-pjk21-d2e073c9ae.json'):
    print("   ✅ File exists: kile-kitabu-firebase-adminsdk-pjk21-d2e073c9ae.json")
else:
    print("   ❌ File does not exist: kile-kitabu-firebase-adminsdk-pjk21-d2e073c9ae.json")
