"""
Exclude verified duplicates from future duplicate detection analysis
This ensures we don't re-analyze the 3,162 already-confirmed duplicates
"""
import pandas as pd
import json
from datetime import datetime

print("=" * 70)
print("DUPLICATE EXCLUSION MECHANISM FOR FUTURE ANALYSIS")
print("=" * 70)

# 1. Load the verified duplicate IDs
print("\n1. LOADING VERIFIED DUPLICATES...")
with open('output/verified_duplicate_arcadia_ids.json', 'r') as f:
    verified_duplicate_ids = json.load(f)
print(f"   Loaded {len(verified_duplicate_ids)} verified duplicate Arcadia IDs")

# 2. Load the current Arcadia database
print("\n2. LOADING ARCADIA DATABASE...")
arcadia_db = pd.read_csv('output/arcadia_database_with_ids.csv')
print(f"   Total Arcadia transactions: {len(arcadia_db)}")

# 3. Create filtered database for future analysis
print("\n3. CREATING FILTERED DATABASE...")
# Mark transactions that are verified duplicates
arcadia_db['is_verified_duplicate'] = arcadia_db['ID'].isin(verified_duplicate_ids)

# Create database excluding verified duplicates
arcadia_filtered = arcadia_db[~arcadia_db['is_verified_duplicate']].copy()
arcadia_filtered = arcadia_filtered.drop('is_verified_duplicate', axis=1)

print(f"   Original transactions: {len(arcadia_db)}")
print(f"   Verified duplicates to exclude: {arcadia_db['is_verified_duplicate'].sum()}")
print(f"   Remaining for analysis: {len(arcadia_filtered)}")

# 4. Save filtered database
output_file = 'output/arcadia_database_excluding_verified.csv'
arcadia_filtered.to_csv(output_file, index=False)
print(f"\n4. SAVED FILTERED DATABASE: {output_file}")

# 5. Create summary report
print("\n5. CREATING SUMMARY REPORT...")
summary = {
    'timestamp': datetime.now().isoformat(),
    'original_arcadia_count': len(arcadia_db),
    'verified_duplicates_excluded': len(verified_duplicate_ids),
    'remaining_for_analysis': len(arcadia_filtered),
    'exclusion_percentage': round(len(verified_duplicate_ids) / len(arcadia_db) * 100, 2),
    'verified_duplicates_file': 'output/verified_duplicate_arcadia_ids.json',
    'filtered_database': output_file
}

with open('output/duplicate_exclusion_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("\n   Summary Report:")
for key, value in summary.items():
    print(f"   - {key}: {value}")

# 6. Verify exclusion integrity
print("\n6. VERIFYING EXCLUSION INTEGRITY...")
# Check that all verified IDs were found and excluded
found_count = arcadia_db['is_verified_duplicate'].sum()
if found_count == len(verified_duplicate_ids):
    print(f"   SUCCESS: All {found_count} verified duplicates successfully excluded")
else:
    missing = len(verified_duplicate_ids) - found_count
    print(f"   WARNING: {missing} verified IDs not found in current database")
    
    # Find which IDs are missing
    missing_ids = set(verified_duplicate_ids) - set(arcadia_db[arcadia_db['is_verified_duplicate']]['ID'])
    if missing_ids and len(missing_ids) < 10:
        print(f"   Missing IDs: {list(missing_ids)[:10]}")

print("\n" + "=" * 70)
print("EXCLUSION MECHANISM READY FOR FUTURE DUPLICATE DETECTION")
print("Use 'arcadia_database_excluding_verified.csv' for future analysis")
print("=" * 70)