#!/usr/bin/env python3
"""
Script to find and delete debts with unknown user names for a specific user ID.
This script will:
1. Find all debts where accountName is 'Unknown' or empty
2. Optionally delete them (with confirmation)
3. Provide a summary of what was found/cleaned
"""

import firebase_admin
from firebase_admin import credentials, db
import sys
import json
from typing import List, Dict, Tuple

# Initialize Firebase
def initialize_firebase():
    """Initialize Firebase connection"""
    try:
        # Check if Firebase is already initialized
        if firebase_admin._apps:
            print("✅ Firebase already initialized")
            return True
        
        # Initialize Firebase
        cred = credentials.Certificate("kilekitabu-firebase-adminsdk-4qj8x-8a8b8c8d8e.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://kilekitabu-default-rtdb.firebaseio.com/'
        })
        
        print("✅ Firebase initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        return False

def find_unknown_debts(user_id: str) -> List[Dict]:
    """
    Find all debts with unknown user names for a specific user ID
    
    Args:
        user_id: The user ID to search for
        
    Returns:
        List of dictionaries containing debt information
    """
    unknown_debts = []
    
    try:
        # Get user debts
        debts_ref = db.reference(f'UserDebts/{user_id}')
        user_debts = debts_ref.get()
        
        if not user_debts:
            print(f"❌ No debts found for user ID: {user_id}")
            return unknown_debts
        
        print(f"🔍 Searching for unknown debts for user: {user_id}")
        print(f"📊 Total phone number groups: {len(user_debts)}")
        
        # Search through all phone number groups
        for phone_number, phone_data in user_debts.items():
            if not isinstance(phone_data, dict) or 'debts' not in phone_data:
                continue
                
            account_name = phone_data.get('accountName', '')
            debts_dict = phone_data.get('debts', {})
            
            # Check if account name is unknown or empty
            if not account_name or account_name.lower() in ['unknown', 'unnamed', '']:
                print(f"⚠️  Found unknown account: {phone_number} -> '{account_name}'")
                
                # Get all debts for this phone number
                for debt_id, debt_data in debts_dict.items():
                    unknown_debt = {
                        'phone_number': phone_number,
                        'account_name': account_name,
                        'debt_id': debt_id,
                        'debt_amount': debt_data.get('debtAmount', '0'),
                        'balance': debt_data.get('balance', '0'),
                        'description': debt_data.get('description', ''),
                        'date': debt_data.get('date', ''),
                        'due_date': debt_data.get('dueDate', 0),
                        'is_complete': debt_data.get('isComplete', False)
                    }
                    unknown_debts.append(unknown_debt)
                    print(f"   📝 Debt: {debt_id} - KSh {debt_data.get('debtAmount', '0')} - {debt_data.get('description', 'No description')}")
        
        print(f"📊 Found {len(unknown_debts)} debts with unknown user names")
        return unknown_debts
        
    except Exception as e:
        print(f"❌ Error finding unknown debts: {e}")
        return []

def delete_unknown_debts(user_id: str, unknown_debts: List[Dict], dry_run: bool = True) -> Tuple[int, int]:
    """
    Delete debts with unknown user names
    
    Args:
        user_id: The user ID
        unknown_debts: List of unknown debts to delete
        dry_run: If True, only show what would be deleted without actually deleting
        
    Returns:
        Tuple of (deleted_count, error_count)
    """
    if not unknown_debts:
        print("ℹ️  No unknown debts to delete")
        return 0, 0
    
    deleted_count = 0
    error_count = 0
    
    try:
        # Get current user debts
        debts_ref = db.reference(f'UserDebts/{user_id}')
        user_debts = debts_ref.get()
        
        if not user_debts:
            print("❌ No user debts found")
            return 0, 0
        
        # Group debts by phone number for efficient deletion
        phone_groups_to_delete = {}
        for debt in unknown_debts:
            phone = debt['phone_number']
            debt_id = debt['debt_id']
            
            if phone not in phone_groups_to_delete:
                phone_groups_to_delete[phone] = []
            phone_groups_to_delete[phone].append(debt_id)
        
        print(f"\n{'🔍 DRY RUN - ' if dry_run else '🗑️  DELETING '}Debts to be processed:")
        
        for phone, debt_ids in phone_groups_to_delete.items():
            print(f"\n📞 Phone: {phone}")
            print(f"   🗑️  Debts to delete: {len(debt_ids)}")
            
            for debt_id in debt_ids:
                print(f"   - {debt_id}")
            
            if not dry_run:
                try:
                    # Delete individual debts
                    for debt_id in debt_ids:
                        if phone in user_debts and 'debts' in user_debts[phone]:
                            if debt_id in user_debts[phone]['debts']:
                                del user_debts[phone]['debts'][debt_id]
                                deleted_count += 1
                                print(f"   ✅ Deleted: {debt_id}")
                            else:
                                print(f"   ⚠️  Debt not found: {debt_id}")
                        else:
                            print(f"   ⚠️  Phone group not found: {phone}")
                    
                    # If no debts left for this phone number, remove the entire phone group
                    if phone in user_debts and 'debts' in user_debts[phone]:
                        if not user_debts[phone]['debts']:
                            del user_debts[phone]
                            print(f"   🗑️  Removed empty phone group: {phone}")
                
                except Exception as e:
                    print(f"   ❌ Error deleting debts for {phone}: {e}")
                    error_count += len(debt_ids)
        
        if not dry_run and deleted_count > 0:
            # Update Firebase with modified data
            debts_ref.set(user_debts)
            print(f"\n✅ Updated Firebase database")
        
        return deleted_count, error_count
        
    except Exception as e:
        print(f"❌ Error deleting unknown debts: {e}")
        return deleted_count, error_count

def print_summary(unknown_debts: List[Dict], deleted_count: int, error_count: int, dry_run: bool):
    """Print a summary of the cleanup operation"""
    print("\n" + "="*60)
    print("📊 CLEANUP SUMMARY")
    print("="*60)
    print(f"🔍 Unknown debts found: {len(unknown_debts)}")
    print(f"💰 Total amount in unknown debts: KSh {sum(float(debt.get('debt_amount', 0)) for debt in unknown_debts):.2f}")
    print(f"📞 Phone numbers affected: {len(set(debt['phone_number'] for debt in unknown_debts))}")
    
    if dry_run:
        print(f"🔍 Mode: DRY RUN (no actual deletions)")
        print(f"ℹ️  Run with --delete to actually delete these debts")
    else:
        print(f"🗑️  Debts deleted: {deleted_count}")
        print(f"❌ Errors: {error_count}")
    
    print("="*60)

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python cleanup_unknown_debts.py <user_id> [--delete]")
        print("  user_id: The user ID to clean up")
        print("  --delete: Actually delete the debts (default is dry run)")
        sys.exit(1)
    
    user_id = sys.argv[1]
    dry_run = '--delete' not in sys.argv
    
    print("🚀 Starting unknown debts cleanup...")
    print(f"👤 User ID: {user_id}")
    print(f"🔍 Mode: {'DRY RUN' if dry_run else 'DELETE'}")
    print("-" * 60)
    
    # Initialize Firebase
    if not initialize_firebase():
        sys.exit(1)
    
    # Find unknown debts
    unknown_debts = find_unknown_debts(user_id)
    
    if not unknown_debts:
        print("✅ No unknown debts found!")
        return
    
    # Delete unknown debts
    deleted_count, error_count = delete_unknown_debts(user_id, unknown_debts, dry_run)
    
    # Print summary
    print_summary(unknown_debts, deleted_count, error_count, dry_run)
    
    if dry_run and unknown_debts:
        print("\n💡 To actually delete these debts, run:")
        print(f"   python cleanup_unknown_debts.py {user_id} --delete")

if __name__ == "__main__":
    main()
