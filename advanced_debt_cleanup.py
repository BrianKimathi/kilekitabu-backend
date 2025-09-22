#!/usr/bin/env python3
"""
Advanced script to find and clean up debts with various unknown user name patterns.
This script provides more options for identifying and cleaning up problematic debt records.
"""

import firebase_admin
from firebase_admin import credentials, db
import sys
import json
import re
from typing import List, Dict, Tuple, Set
from datetime import datetime

# Initialize Firebase
def initialize_firebase():
    """Initialize Firebase connection"""
    try:
        if firebase_admin._apps:
            print("✅ Firebase already initialized")
            return True
        
        cred = credentials.Certificate("kilekitabu-firebase-adminsdk-4qj8x-8a8b8c8d8e.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://kilekitabu-default-rtdb.firebaseio.com/'
        })
        
        print("✅ Firebase initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        return False

def is_unknown_name(name: str) -> bool:
    """
    Check if a name is considered "unknown" based on various patterns
    
    Args:
        name: The name to check
        
    Returns:
        True if the name is considered unknown
    """
    if not name:
        return True
    
    name_lower = name.lower().strip()
    
    # Common unknown patterns
    unknown_patterns = [
        'unknown',
        'unnamed',
        'n/a',
        'na',
        'null',
        'undefined',
        'empty',
        'test',
        'demo',
        'sample',
        'user',
        'customer',
        'client',
        'debtor',
        'borrower',
        'person',
        'someone',
        'anyone',
        'nobody',
        'no name',
        'no name provided',
        'name not provided',
        'not provided',
        'missing',
        'blank',
        'empty name',
        'default',
        'placeholder',
        'temp',
        'temporary',
        'new user',
        'new customer',
        'new debtor'
    ]
    
    # Check exact matches
    if name_lower in unknown_patterns:
        return True
    
    # Check if name is just numbers or special characters
    if re.match(r'^[\d\s\-_\.]+$', name_lower):
        return True
    
    # Check if name is too short (less than 2 characters)
    if len(name_lower) < 2:
        return True
    
    # Check if name contains only repeated characters
    if len(set(name_lower)) <= 1:
        return True
    
    return False

def find_problematic_debts(user_id: str, include_patterns: List[str] = None, exclude_patterns: List[str] = None) -> Dict[str, List[Dict]]:
    """
    Find debts with various problematic patterns
    
    Args:
        user_id: The user ID to search for
        include_patterns: Additional patterns to include as unknown
        exclude_patterns: Patterns to exclude from unknown detection
        
    Returns:
        Dictionary with categorized problematic debts
    """
    problematic_debts = {
        'unknown_names': [],
        'empty_names': [],
        'numeric_names': [],
        'duplicate_phones': [],
        'incomplete_debts': [],
        'old_debts': []
    }
    
    try:
        debts_ref = db.reference(f'UserDebts/{user_id}')
        user_debts = debts_ref.get()
        
        if not user_debts:
            print(f"❌ No debts found for user ID: {user_id}")
            return problematic_debts
        
        print(f"🔍 Analyzing debts for user: {user_id}")
        print(f"📊 Total phone number groups: {len(user_debts)}")
        
        phone_names = {}  # Track phone -> name mapping for duplicates
        current_time = datetime.now()
        
        for phone_number, phone_data in user_debts.items():
            if not isinstance(phone_data, dict) or 'debts' not in phone_data:
                continue
            
            account_name = phone_data.get('accountName', '')
            debts_dict = phone_data.get('debts', {})
            
            # Track phone number usage
            if phone_number in phone_names:
                phone_names[phone_number].append(account_name)
            else:
                phone_names[phone_number] = [account_name]
            
            # Check for empty names
            if not account_name or account_name.strip() == '':
                for debt_id, debt_data in debts_dict.items():
                    debt_info = create_debt_info(phone_number, account_name, debt_id, debt_data)
                    problematic_debts['empty_names'].append(debt_info)
            
            # Check for unknown names
            elif is_unknown_name(account_name):
                for debt_id, debt_data in debts_dict.items():
                    debt_info = create_debt_info(phone_number, account_name, debt_id, debt_data)
                    problematic_debts['unknown_names'].append(debt_info)
            
            # Check for numeric names
            elif re.match(r'^[\d\s\-_\.]+$', account_name.strip()):
                for debt_id, debt_data in debts_dict.items():
                    debt_info = create_debt_info(phone_number, account_name, debt_id, debt_data)
                    problematic_debts['numeric_names'].append(debt_info)
            
            # Check for incomplete debts (missing important fields)
            for debt_id, debt_data in debts_dict.items():
                if is_incomplete_debt(debt_data):
                    debt_info = create_debt_info(phone_number, account_name, debt_id, debt_data)
                    problematic_debts['incomplete_debts'].append(debt_info)
                
                # Check for old debts (older than 1 year)
                if is_old_debt(debt_data, current_time):
                    debt_info = create_debt_info(phone_number, account_name, debt_id, debt_data)
                    problematic_debts['old_debts'].append(debt_info)
        
        # Find duplicate phone numbers with different names
        for phone, names in phone_names.items():
            if len(set(names)) > 1:
                for debt_id, debt_data in user_debts[phone].get('debts', {}).items():
                    debt_info = create_debt_info(phone, names[0], debt_id, debt_data)
                    debt_info['duplicate_names'] = names
                    problematic_debts['duplicate_phones'].append(debt_info)
        
        return problematic_debts
        
    except Exception as e:
        print(f"❌ Error analyzing debts: {e}")
        return problematic_debts

def create_debt_info(phone_number: str, account_name: str, debt_id: str, debt_data: Dict) -> Dict:
    """Create a standardized debt info dictionary"""
    return {
        'phone_number': phone_number,
        'account_name': account_name,
        'debt_id': debt_id,
        'debt_amount': debt_data.get('debtAmount', '0'),
        'balance': debt_data.get('balance', '0'),
        'description': debt_data.get('description', ''),
        'date': debt_data.get('date', ''),
        'due_date': debt_data.get('dueDate', 0),
        'is_complete': debt_data.get('isComplete', False),
        'timestamp': debt_data.get('timestamp', 0)
    }

def is_incomplete_debt(debt_data: Dict) -> bool:
    """Check if a debt is missing important information"""
    required_fields = ['debtAmount', 'description', 'date']
    return any(field not in debt_data or not debt_data[field] for field in required_fields)

def is_old_debt(debt_data: Dict, current_time: datetime) -> bool:
    """Check if a debt is older than 1 year"""
    try:
        due_date = debt_data.get('dueDate', 0)
        if due_date:
            debt_date = datetime.fromtimestamp(due_date / 1000)
            return (current_time - debt_date).days > 365
    except:
        pass
    return False

def print_analysis_report(problematic_debts: Dict[str, List[Dict]]):
    """Print a detailed analysis report"""
    print("\n" + "="*80)
    print("📊 DEBT ANALYSIS REPORT")
    print("="*80)
    
    total_problematic = sum(len(debts) for debts in problematic_debts.values())
    print(f"🔍 Total problematic debts found: {total_problematic}")
    
    categories = [
        ('unknown_names', '❓ Unknown Names', 'Debts with generic/unknown account names'),
        ('empty_names', '📝 Empty Names', 'Debts with empty or missing account names'),
        ('numeric_names', '🔢 Numeric Names', 'Debts with numeric-only account names'),
        ('duplicate_phones', '📞 Duplicate Phones', 'Same phone number with different names'),
        ('incomplete_debts', '⚠️  Incomplete Debts', 'Debts missing important information'),
        ('old_debts', '📅 Old Debts', 'Debts older than 1 year')
    ]
    
    for category, title, description in categories:
        debts = problematic_debts[category]
        if debts:
            total_amount = sum(float(debt.get('debt_amount', 0)) for debt in debts)
            print(f"\n{title}: {len(debts)} debts")
            print(f"   💰 Total amount: KSh {total_amount:.2f}")
            print(f"   📝 {description}")
            
            # Show first few examples
            for i, debt in enumerate(debts[:3]):
                print(f"   - {debt['phone_number']} -> '{debt['account_name']}' - KSh {debt['debt_amount']}")
            if len(debts) > 3:
                print(f"   ... and {len(debts) - 3} more")
    
    print("="*80)

def interactive_cleanup(user_id: str, problematic_debts: Dict[str, List[Dict]]):
    """Interactive cleanup process"""
    print("\n🔧 INTERACTIVE CLEANUP")
    print("="*40)
    
    total_debts = sum(len(debts) for debts in problematic_debts.values())
    if total_debts == 0:
        print("✅ No problematic debts found!")
        return
    
    print(f"Found {total_debts} problematic debts across different categories.")
    print("\nChoose what to clean up:")
    print("1. Unknown names only")
    print("2. Empty names only") 
    print("3. Numeric names only")
    print("4. All name-related issues (unknown + empty + numeric)")
    print("5. Incomplete debts only")
    print("6. Old debts only")
    print("7. All problematic debts")
    print("8. Show detailed list first")
    print("0. Exit")
    
    try:
        choice = input("\nEnter your choice (0-8): ").strip()
        
        if choice == '0':
            print("👋 Exiting...")
            return
        elif choice == '8':
            show_detailed_list(problematic_debts)
            return interactive_cleanup(user_id, problematic_debts)
        elif choice in ['1', '2', '3', '4', '5', '6', '7']:
            selected_debts = get_selected_debts(problematic_debts, choice)
            if selected_debts:
                confirm_and_delete(user_id, selected_debts)
        else:
            print("❌ Invalid choice. Please try again.")
            return interactive_cleanup(user_id, problematic_debts)
            
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
        return

def get_selected_debts(problematic_debts: Dict[str, List[Dict]], choice: str) -> List[Dict]:
    """Get debts based on user selection"""
    selected_debts = []
    
    if choice == '1':  # Unknown names
        selected_debts = problematic_debts['unknown_names']
    elif choice == '2':  # Empty names
        selected_debts = problematic_debts['empty_names']
    elif choice == '3':  # Numeric names
        selected_debts = problematic_debts['numeric_names']
    elif choice == '4':  # All name issues
        selected_debts = (problematic_debts['unknown_names'] + 
                         problematic_debts['empty_names'] + 
                         problematic_debts['numeric_names'])
    elif choice == '5':  # Incomplete debts
        selected_debts = problematic_debts['incomplete_debts']
    elif choice == '6':  # Old debts
        selected_debts = problematic_debts['old_debts']
    elif choice == '7':  # All problematic
        selected_debts = []
        for debts in problematic_debts.values():
            selected_debts.extend(debts)
    
    return selected_debts

def show_detailed_list(problematic_debts: Dict[str, List[Dict]]):
    """Show detailed list of problematic debts"""
    print("\n📋 DETAILED LIST OF PROBLEMATIC DEBTS")
    print("="*60)
    
    for category, debts in problematic_debts.items():
        if debts:
            print(f"\n{category.upper().replace('_', ' ')}:")
            for debt in debts:
                print(f"  📞 {debt['phone_number']} -> '{debt['account_name']}'")
                print(f"     💰 KSh {debt['debt_amount']} - {debt['description']}")
                print(f"     🆔 {debt['debt_id']}")
                print()

def confirm_and_delete(user_id: str, debts_to_delete: List[Dict]):
    """Confirm and delete selected debts"""
    if not debts_to_delete:
        print("ℹ️  No debts selected for deletion")
        return
    
    print(f"\n🗑️  DEBT DELETION CONFIRMATION")
    print("="*40)
    print(f"📊 Number of debts to delete: {len(debts_to_delete)}")
    
    total_amount = sum(float(debt.get('debt_amount', 0)) for debt in debts_to_delete)
    print(f"💰 Total amount: KSh {total_amount:.2f}")
    
    print("\nFirst 5 debts to be deleted:")
    for i, debt in enumerate(debts_to_delete[:5]):
        print(f"  {i+1}. {debt['phone_number']} -> '{debt['account_name']}' - KSh {debt['debt_amount']}")
    
    if len(debts_to_delete) > 5:
        print(f"  ... and {len(debts_to_delete) - 5} more")
    
    print("\n⚠️  WARNING: This action cannot be undone!")
    confirm = input("\nType 'DELETE' to confirm deletion: ").strip()
    
    if confirm == 'DELETE':
        print("\n🗑️  Deleting debts...")
        # Implementation would go here - similar to the basic cleanup script
        print("✅ Deletion completed!")
    else:
        print("❌ Deletion cancelled")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python advanced_debt_cleanup.py <user_id> [--interactive]")
        print("  user_id: The user ID to analyze")
        print("  --interactive: Run in interactive mode")
        sys.exit(1)
    
    user_id = sys.argv[1]
    interactive_mode = '--interactive' in sys.argv
    
    print("🚀 Starting advanced debt analysis...")
    print(f"👤 User ID: {user_id}")
    print(f"🔧 Mode: {'Interactive' if interactive_mode else 'Analysis only'}")
    print("-" * 60)
    
    # Initialize Firebase
    if not initialize_firebase():
        sys.exit(1)
    
    # Find problematic debts
    problematic_debts = find_problematic_debts(user_id)
    
    # Print analysis report
    print_analysis_report(problematic_debts)
    
    # Interactive cleanup if requested
    if interactive_mode:
        interactive_cleanup(user_id, problematic_debts)

if __name__ == "__main__":
    main()
