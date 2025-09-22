# Debt Cleanup Scripts

This directory contains scripts to help clean up problematic debt records in the Firebase database.

## Scripts Available

### 1. `cleanup_unknown_debts.py` - Basic Cleanup

A simple script to find and delete debts with unknown user names.

**Usage:**

```bash
# Dry run (recommended first)
python cleanup_unknown_debts.py <user_id>

# Actually delete the debts
python cleanup_unknown_debts.py <user_id> --delete
```

**Example:**

```bash
# First, see what would be deleted
python cleanup_unknown_debts.py GI7PPaaRh7hRogozJcDHt33RQEw2

# If you're satisfied with the results, actually delete them
python cleanup_unknown_debts.py GI7PPaaRh7hRogozJcDHt33RQEw2 --delete
```

### 2. `advanced_debt_cleanup.py` - Advanced Analysis

A comprehensive script that analyzes debts for various problematic patterns.

**Usage:**

```bash
# Analysis only
python advanced_debt_cleanup.py <user_id>

# Interactive mode
python advanced_debt_cleanup.py <user_id> --interactive
```

**Example:**

```bash
# Analyze all debts for issues
python advanced_debt_cleanup.py GI7PPaaRh7hRogozJcDHt33RQEw2

# Interactive cleanup with guided options
python advanced_debt_cleanup.py GI7PPaaRh7hRogozJcDHt33RQEw2 --interactive
```

## What These Scripts Find

### Basic Script (`cleanup_unknown_debts.py`)

- Debts where `accountName` is empty, "Unknown", or similar generic values

### Advanced Script (`advanced_debt_cleanup.py`)

- **Unknown Names**: Generic names like "Unknown", "User", "Customer", etc.
- **Empty Names**: Missing or empty account names
- **Numeric Names**: Names that are just numbers or special characters
- **Duplicate Phones**: Same phone number with different names
- **Incomplete Debts**: Debts missing important information
- **Old Debts**: Debts older than 1 year

## Safety Features

1. **Dry Run by Default**: Both scripts show what would be deleted without actually deleting
2. **Confirmation Required**: Interactive mode requires explicit confirmation
3. **Detailed Reporting**: Shows exactly what will be affected
4. **Backup Recommended**: Always backup your database before running cleanup scripts

## Database Structure

The scripts work with the following Firebase structure:

```
UserDebts/
  {user_id}/
    {phone_number}/
      accountName: "Account Name"
      phoneNumber: "+254..."
      debts/
        {debt_id}/
          debtAmount: "1000.00"
          balance: "1000.00"
          description: "Debt description"
          date: "01/01/2024"
          dueDate: 1704067200000
          isComplete: false
```

## Prerequisites

1. Firebase credentials file (`kilekitabu-firebase-adminsdk-4qj8x-8a8b8c8d8e.json`)
2. Python 3.6+
3. Firebase Admin SDK: `pip install firebase-admin`

## Running the Scripts

1. Navigate to the backend directory:

   ```bash
   cd kilekitabu-backend
   ```

2. Run the script with your user ID:

   ```bash
   python cleanup_unknown_debts.py YOUR_USER_ID
   ```

3. Review the output and run with `--delete` if satisfied:
   ```bash
   python cleanup_unknown_debts.py YOUR_USER_ID --delete
   ```

## Output Example

```
🚀 Starting unknown debts cleanup...
👤 User ID: GI7PPaaRh7hRogozJcDHt33RQEw2
🔍 Mode: DRY RUN
------------------------------------------------------------
✅ Firebase initialized successfully
🔍 Searching for unknown debts for user: GI7PPaaRh7hRogozJcDHt33RQEw2
📊 Total phone number groups: 15
⚠️  Found unknown account: +254700000001 -> 'Unknown'
   📝 Debt: debt_123 - KSh 500.00 - Milk debt
⚠️  Found unknown account: +254700000002 -> ''
   📝 Debt: debt_456 - KSh 1000.00 - Sugar debt
📊 Found 2 debts with unknown user names

🔍 DRY RUN - Debts to be processed:

📞 Phone: +254700000001
   🗑️  Debts to delete: 1
   - debt_123

📞 Phone: +254700000002
   🗑️  Debts to delete: 1
   - debt_456

============================================================
📊 CLEANUP SUMMARY
============================================================
🔍 Unknown debts found: 2
💰 Total amount in unknown debts: KSh 1500.00
📞 Phone numbers affected: 2
🔍 Mode: DRY RUN (no actual deletions)
ℹ️  Run with --delete to actually delete these debts
============================================================

💡 To actually delete these debts, run:
   python cleanup_unknown_debts.py GI7PPaaRh7hRogozJcDHt33RQEw2 --delete
```

## Troubleshooting

1. **Firebase Connection Issues**: Ensure the credentials file is in the correct location
2. **Permission Errors**: Make sure the Firebase service account has read/write permissions
3. **User ID Not Found**: Verify the user ID exists in the database
4. **No Debts Found**: The user might not have any debts or they might all be properly named

## Support

If you encounter any issues, check:

1. Firebase credentials are correct
2. User ID is valid
3. Database permissions are set correctly
4. Python dependencies are installed
