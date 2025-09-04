"""
Remove pre-2020 transactions from arcadia_database_excluding_verified.csv
This is done VERY CAREFULLY with multiple verification steps
"""
import pandas as pd
from datetime import datetime

print("=" * 70)
print("REMOVING PRE-2020 TRANSACTIONS FROM FILTERED DATABASE")
print("=" * 70)

# 1. Load the current file
print("\n1. LOADING CURRENT FILE...")
file_path = 'output/arcadia_database_excluding_verified.csv'
df = pd.read_csv(file_path)
print(f"   Loaded {len(df)} transactions from {file_path}")

# 2. Convert date column and analyze
print("\n2. ANALYZING DATE DISTRIBUTION...")
df['Announcement date*'] = pd.to_datetime(df['Announcement date*'])

# Count pre-2020 transactions
pre_2020 = df[df['Announcement date*'] < '2020-01-01']
post_2020 = df[df['Announcement date*'] >= '2020-01-01']

print(f"   Pre-2020 transactions: {len(pre_2020)}")
print(f"   Post-2020 transactions: {len(post_2020)}")
print(f"   Total: {len(df)}")

# 3. Verify we have exactly 36 pre-2020 transactions
print("\n3. VERIFICATION CHECK...")
if len(pre_2020) != 36:
    print(f"   ERROR: Expected 36 pre-2020 transactions, found {len(pre_2020)}")
    print("   ABORTING to prevent data corruption")
    exit(1)
else:
    print(f"   SUCCESS: Found exactly 36 pre-2020 transactions as expected")

# 4. Show what will be removed
print("\n4. TRANSACTIONS TO BE REMOVED:")
print("   " + "-" * 60)
print("   Date Range:", pre_2020['Announcement date*'].min(), "to", pre_2020['Announcement date*'].max())
print("\n   Status distribution of removed transactions:")
print(pre_2020['Status*'].value_counts().to_string().replace('\n', '\n   '))

print("\n   Sample of transactions being removed (first 5):")
display_cols = ['ID', 'Announcement date*', 'Target Company', 'Transaction Size*, $M', 'Status*']
print(pre_2020[display_cols].head().to_string().replace('\n', '\n   '))

# 5. Create filtered dataframe (keep only 2020 onwards)
print("\n5. FILTERING TRANSACTIONS...")
df_filtered = df[df['Announcement date*'] >= '2020-01-01'].copy()
print(f"   Keeping {len(df_filtered)} transactions from 2020-01-01 onwards")

# 6. Final verification
print("\n6. FINAL VERIFICATION...")
expected_count = 445
if len(df_filtered) != expected_count:
    print(f"   ERROR: Expected {expected_count} transactions after filtering, got {len(df_filtered)}")
    print("   ABORTING to prevent data corruption")
    exit(1)
else:
    print(f"   SUCCESS: Have exactly {expected_count} transactions as expected")

# Verify date range
min_date = df_filtered['Announcement date*'].min()
max_date = df_filtered['Announcement date*'].max()
print(f"   New date range: {min_date} to {max_date}")

if min_date < pd.Timestamp('2020-01-01'):
    print(f"   ERROR: Found dates before 2020-01-01 in filtered data!")
    print("   ABORTING to prevent data corruption")
    exit(1)

# 7. Save the filtered data
print("\n7. SAVING FILTERED DATA...")
# Convert datetime back to string format for CSV
df_filtered['Announcement date*'] = df_filtered['Announcement date*'].dt.strftime('%Y-%m-%d')
df_filtered.to_csv(file_path, index=False)
print(f"   Saved {len(df_filtered)} transactions to {file_path}")

# 8. Summary
print("\n8. OPERATION SUMMARY:")
print("   " + "=" * 60)
print(f"   Original count: {len(df)} transactions")
print(f"   Removed: {len(pre_2020)} pre-2020 transactions")
print(f"   Final count: {len(df_filtered)} transactions")
print(f"   Date range: 2020-01-01 to {max_date.strftime('%Y-%m-%d')}")
print("\n   SUCCESS: Pre-2020 transactions have been carefully removed")

# 9. Create a backup record of what was removed
removed_record_file = 'output/removed_pre_2020_transactions.csv'
pre_2020['Announcement date*'] = pre_2020['Announcement date*'].dt.strftime('%Y-%m-%d')
pre_2020.to_csv(removed_record_file, index=False)
print(f"\n   Backup of removed transactions saved to: {removed_record_file}")

print("\n" + "=" * 70)
print("OPERATION COMPLETE - DATABASE NOW CONTAINS ONLY 2020+ TRANSACTIONS")
print("=" * 70)