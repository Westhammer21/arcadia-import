"""
CRITICAL TASK: Exclude verified duplicate transactions from InvestGame database
Creates new file with only unanalyzed transactions
"""
import pandas as pd
import json
from datetime import datetime

print("=" * 70)
print("EXCLUDING VERIFIED DUPLICATES FROM INVESTGAME DATABASE")
print("CRITICAL: This removes already-analyzed transactions")
print("=" * 70)

# 1. Load InvestGame database with IG_ID
print("\n1. LOADING INVESTGAME DATABASE...")
ig_db = pd.read_csv('src/investgame_database_clean_with_IG_ID.csv')
print(f"   Loaded {len(ig_db)} transactions")
print(f"   IG_ID range: {ig_db['IG_ID'].min()} to {ig_db['IG_ID'].max()}")

# 2. Load verified duplicates to get ig_ids to exclude
print("\n2. LOADING VERIFIED DUPLICATES...")
verified = pd.read_csv('output/Correct Transaction Imported.csv', sep='\t', encoding='utf-8')
print(f"   Loaded {len(verified)} verified duplicate records")

# Get unique ig_ids (these are the ones to EXCLUDE)
exclude_ids = verified['ig_id'].dropna().unique()
exclude_ids = [int(id) for id in exclude_ids]  # Ensure integers
print(f"   Unique ig_ids to exclude: {len(exclude_ids)}")

# 3. Verification before filtering
print("\n3. PRE-FILTERING VERIFICATION...")
print(f"   Original InvestGame transactions: {len(ig_db)}")
print(f"   Transactions to exclude: {len(exclude_ids)}")
print(f"   Expected remaining: {len(ig_db) - len(exclude_ids)}")

# Check that all exclude_ids exist in IG_ID column
missing_ids = [id for id in exclude_ids if id not in ig_db['IG_ID'].values]
if missing_ids:
    print(f"   WARNING: {len(missing_ids)} ig_ids not found in IG_ID column")
    if len(missing_ids) <= 10:
        print(f"   Missing IDs: {missing_ids}")
else:
    print(f"   SUCCESS: All {len(exclude_ids)} ig_ids found in database")

# 4. Filter the database - KEEP only rows NOT in exclude list
print("\n4. FILTERING DATABASE...")
print(f"   Excluding IG_IDs that match verified duplicates...")
ig_filtered = ig_db[~ig_db['IG_ID'].isin(exclude_ids)].copy()
print(f"   Filtered database has {len(ig_filtered)} transactions")

# 5. Verification after filtering
print("\n5. POST-FILTERING VERIFICATION...")
excluded_count = len(ig_db) - len(ig_filtered)
print(f"   Transactions excluded: {excluded_count}")
print(f"   Transactions remaining: {len(ig_filtered)}")

# Verify the math
expected_remaining = len(ig_db) - len(exclude_ids)
actual_remaining = len(ig_filtered)
if expected_remaining == actual_remaining:
    print(f"   SUCCESS: Count matches expected ({expected_remaining})")
else:
    print(f"   WARNING: Expected {expected_remaining}, got {actual_remaining}")
    print(f"   Difference: {abs(expected_remaining - actual_remaining)}")

# Double-check: None of the excluded IDs should be in filtered data
remaining_ids = ig_filtered['IG_ID'].values
overlap = set(exclude_ids) & set(remaining_ids)
if overlap:
    print(f"   ERROR: {len(overlap)} excluded IDs still in filtered data!")
else:
    print(f"   SUCCESS: No excluded IDs remain in filtered data")

# 6. Sample verification
print("\n6. SAMPLE VERIFICATION...")
# Check first few excluded IDs are NOT in filtered
sample_excluded = exclude_ids[:5]
print(f"   Checking excluded IDs are gone:")
for id in sample_excluded:
    in_original = id in ig_db['IG_ID'].values
    in_filtered = id in ig_filtered['IG_ID'].values
    target = ig_db[ig_db['IG_ID'] == id]['Target name'].iloc[0] if in_original else "N/A"
    print(f"   ID {id:4} ({target[:20]}...): Original={in_original}, Filtered={in_filtered}")

# Check some non-excluded IDs ARE in filtered
print(f"\n   Checking non-excluded IDs remain:")
all_ids = set(ig_db['IG_ID'].values)
non_excluded = list(all_ids - set(exclude_ids))[:5]
for id in non_excluded:
    in_filtered = id in ig_filtered['IG_ID'].values
    target = ig_db[ig_db['IG_ID'] == id]['Target name'].iloc[0]
    print(f"   ID {id:4} ({target[:20]}...): In filtered={in_filtered}")

# 7. Save filtered database
print("\n7. SAVING FILTERED DATABASE...")
output_file = 'src/investgame_database_excluding_verified.csv'
ig_filtered.to_csv(output_file, index=False)
print(f"   Saved to: {output_file}")
print(f"   Total rows: {len(ig_filtered)}")

# 8. Save exclusion audit log
print("\n8. CREATING AUDIT LOG...")
audit = {
    'timestamp': datetime.now().isoformat(),
    'original_investgame_count': len(ig_db),
    'verified_duplicates_count': len(verified),
    'unique_ids_excluded': len(exclude_ids),
    'final_filtered_count': len(ig_filtered),
    'excluded_transaction_count': excluded_count,
    'verification_passed': excluded_count == len(exclude_ids),
    'no_overlap_check': len(overlap) == 0,
    'source_files': {
        'investgame': 'src/investgame_database_clean_with_IG_ID.csv',
        'verified': 'output/Correct Transaction Imported.csv'
    },
    'output_file': output_file
}

audit_file = 'output/investgame_exclusion_audit.json'
with open(audit_file, 'w') as f:
    json.dump(audit, f, indent=2)
print(f"   Audit log saved to: {audit_file}")

# Also save list of excluded IDs for reference
excluded_ids_file = 'output/excluded_investgame_ids.json'
with open(excluded_ids_file, 'w') as f:
    json.dump(sorted(exclude_ids), f, indent=2)
print(f"   Excluded IDs list saved to: {excluded_ids_file}")

# 9. Summary statistics
print("\n9. FINAL SUMMARY:")
print("   " + "=" * 60)
print(f"   ORIGINAL: {len(ig_db)} transactions in InvestGame")
print(f"   EXCLUDED: {excluded_count} verified duplicates")
print(f"   REMAINING: {len(ig_filtered)} unanalyzed transactions")
print(f"   " + "-" * 60)

# Date range of remaining transactions
ig_filtered['Date'] = pd.to_datetime(ig_filtered['Date'])
print(f"   Date range of remaining: {ig_filtered['Date'].min()} to {ig_filtered['Date'].max()}")

# Category distribution of remaining
print(f"\n   Category distribution of remaining transactions:")
for cat, count in ig_filtered['Category'].value_counts().head().items():
    print(f"   - {cat}: {count}")

print("\n" + "=" * 70)
print("EXCLUSION COMPLETE - FILTERED DATABASE READY")
print(f"Use '{output_file}' for future duplicate detection")
print("=" * 70)