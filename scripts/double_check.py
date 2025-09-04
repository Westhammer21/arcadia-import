"""
CRITICAL VERIFICATION: Double-check that exclusion was done correctly
This is a case-sensitive task - must be 100% accurate
"""
import pandas as pd
import numpy as np
import json

print("=" * 80)
print("DOUBLE-CHECKING EXCLUSION OF VERIFIED DUPLICATES")
print("CRITICAL VERIFICATION - MUST BE 100% ACCURATE")
print("=" * 80)

# Track all verification results
verification_results = []

# 1. Load all three databases
print("\n1. LOADING ALL DATABASES...")
print("-" * 60)

# Original InvestGame with IG_ID
original = pd.read_csv('src/investgame_database_clean_with_IG_ID.csv')
print(f"   Original InvestGame: {len(original)} transactions")
print(f"   IG_ID range: {original['IG_ID'].min()} to {original['IG_ID'].max()}")

# Verified duplicates (tab-delimited)
verified = pd.read_csv('output/Correct Transaction Imported.csv', sep='\t', encoding='utf-8')
print(f"   Verified duplicates: {len(verified)} records")
verified_ids = verified['ig_id'].dropna().unique()
verified_ids = [int(id) for id in verified_ids]
print(f"   Unique ig_ids in verified: {len(verified_ids)}")

# Filtered InvestGame (after exclusion)
filtered = pd.read_csv('src/investgame_database_excluding_verified.csv')
print(f"   Filtered InvestGame: {len(filtered)} transactions")
print(f"   IG_ID range: {filtered['IG_ID'].min()} to {filtered['IG_ID'].max()}")

# 2. Mathematical verification
print("\n2. MATHEMATICAL VERIFICATION...")
print("-" * 60)
expected = len(original) - len(verified_ids)
actual = len(filtered)
math_check = expected == actual

print(f"   Original count: {len(original)}")
print(f"   Minus excluded: {len(verified_ids)}")
print(f"   Expected result: {expected}")
print(f"   Actual result: {actual}")
print(f"   PASS" if math_check else f"   FAIL: Difference of {abs(expected-actual)}")
verification_results.append(("Mathematical verification", math_check))

# 3. Set theory verification - NO OVERLAP
print("\n3. SET THEORY VERIFICATION - NO OVERLAP...")
print("-" * 60)
filtered_ids = set(filtered['IG_ID'].values)
verified_ids_set = set(verified_ids)
overlap = filtered_ids & verified_ids_set
no_overlap = len(overlap) == 0

print(f"   Filtered IDs: {len(filtered_ids)}")
print(f"   Verified IDs: {len(verified_ids_set)}")
print(f"   Overlap: {len(overlap)}")
if overlap and len(overlap) <= 10:
    print(f"   Overlapping IDs: {list(overlap)[:10]}")
print(f"   PASS - No overlap" if no_overlap else f"   FAIL - {len(overlap)} IDs in both sets")
verification_results.append(("No overlap check", no_overlap))

# 4. Union verification - filtered + excluded = original
print("\n4. UNION VERIFICATION - COMPLETENESS CHECK...")
print("-" * 60)
original_ids = set(original['IG_ID'].values)
union = filtered_ids | verified_ids_set
union_complete = union == original_ids

print(f"   Original IDs: {len(original_ids)}")
print(f"   Union of filtered + excluded: {len(union)}")
print(f"   Missing from union: {len(original_ids - union)}")
print(f"   Extra in union: {len(union - original_ids)}")
print(f"   PASS - Complete" if union_complete else f"   FAIL - Mismatch")
verification_results.append(("Union completeness", union_complete))

# 5. Specific ID spot checks
print("\n5. SPECIFIC ID VERIFICATION...")
print("-" * 60)

# Check that specific verified IDs are NOT in filtered
test_verified_ids = [0, 1, 5, 100, 1000, 2000, 3000]  # Known verified IDs
print("   Checking verified IDs are excluded:")
all_excluded_correctly = True
for id in test_verified_ids:
    if id in verified_ids_set:
        in_filtered = id in filtered_ids
        if in_filtered:
            all_excluded_correctly = False
        status = "STILL IN FILTERED" if in_filtered else "Correctly excluded"
        target = original[original['IG_ID'] == id]['Target name'].iloc[0] if id in original_ids else "N/A"
        print(f"   ID {id:4} ({target[:20]:<20}): {status}")

verification_results.append(("Verified IDs excluded", all_excluded_correctly))

# Check that some non-verified IDs ARE in filtered
print("\n   Checking non-verified IDs are retained:")
non_verified_ids = list(original_ids - verified_ids_set)[:7]
all_retained_correctly = True
for id in non_verified_ids:
    in_filtered = id in filtered_ids
    if not in_filtered:
        all_retained_correctly = False
    status = "Correctly retained" if in_filtered else "MISSING"
    target = original[original['IG_ID'] == id]['Target name'].iloc[0]
    print(f"   ID {id:4} ({target[:20]:<20}): {status}")

verification_results.append(("Non-verified IDs retained", all_retained_correctly))

# 6. Data integrity check
print("\n6. DATA INTEGRITY CHECK...")
print("-" * 60)

# Check columns are preserved
cols_match = list(original.columns) == list(filtered.columns)
print(f"   Columns preserved: {'PASS' if cols_match else 'FAIL'}")
if not cols_match:
    print(f"   Original columns: {list(original.columns)}")
    print(f"   Filtered columns: {list(filtered.columns)}")
verification_results.append(("Columns preserved", cols_match))

# Check a specific row's data integrity
test_id = non_verified_ids[0] if non_verified_ids else None
if test_id:
    orig_row = original[original['IG_ID'] == test_id].iloc[0]
    filt_row = filtered[filtered['IG_ID'] == test_id].iloc[0]
    
    # Compare key fields
    fields_to_check = ['Target name', 'Date', 'Type', 'Category', 'Size, $m']
    data_intact = True
    print(f"\n   Checking data integrity for ID {test_id}:")
    for field in fields_to_check:
        if field in orig_row and field in filt_row:
            match = str(orig_row[field]) == str(filt_row[field])
            if not match:
                data_intact = False
            status = "OK" if match else "FAIL"
            print(f"   {field:20}: {status} ('{orig_row[field]}' vs '{filt_row[field]}')")
    
    verification_results.append(("Data integrity", data_intact))

# 7. Cross-reference with exclusion audit
print("\n7. CROSS-REFERENCE WITH AUDIT LOG...")
print("-" * 60)
try:
    with open('output/investgame_exclusion_audit.json', 'r') as f:
        audit = json.load(f)
    
    print(f"   Audit log verification:")
    print(f"   - Original count: {audit['original_investgame_count']} (actual: {len(original)})")
    print(f"   - Excluded count: {audit['unique_ids_excluded']} (actual: {len(verified_ids)})")
    print(f"   - Final count: {audit['final_filtered_count']} (actual: {len(filtered)})")
    
    audit_match = (
        audit['original_investgame_count'] == len(original) and
        audit['unique_ids_excluded'] == len(verified_ids) and
        audit['final_filtered_count'] == len(filtered)
    )
    print(f"   Audit consistency: {'PASS' if audit_match else 'FAIL'}")
    verification_results.append(("Audit consistency", audit_match))
except Exception as e:
    print(f"   Could not load audit log: {e}")

# 8. Random sampling verification
print("\n8. RANDOM SAMPLING VERIFICATION...")
print("-" * 60)
import random
random.seed(123)  # For reproducibility

# Sample 20 random verified IDs - should NOT be in filtered
sample_verified = random.sample(verified_ids, min(20, len(verified_ids)))
verified_excluded_count = sum(1 for id in sample_verified if id not in filtered_ids)
print(f"   Sampled {len(sample_verified)} verified IDs:")
print(f"   - Correctly excluded: {verified_excluded_count}/{len(sample_verified)}")

# Sample 20 random filtered IDs - should NOT be in verified
sample_filtered = random.sample(list(filtered_ids), min(20, len(filtered_ids)))
filtered_not_verified = sum(1 for id in sample_filtered if id not in verified_ids_set)
print(f"   Sampled {len(sample_filtered)} filtered IDs:")
print(f"   - Correctly retained (not in verified): {filtered_not_verified}/{len(sample_filtered)}")

random_check = (verified_excluded_count == len(sample_verified) and 
                filtered_not_verified == len(sample_filtered))
verification_results.append(("Random sampling", random_check))

# 9. Final summary
print("\n" + "=" * 80)
print("FINAL VERIFICATION SUMMARY")
print("=" * 80)

all_passed = all(result for _, result in verification_results)
passed_count = sum(1 for _, result in verification_results if result)

print(f"\nVerification Results: {passed_count}/{len(verification_results)} checks passed")
print("-" * 60)
for check_name, passed in verification_results:
    status = "PASS" if passed else "FAIL"
    print(f"   {check_name:30}: {status}")

print("\n" + "=" * 80)
if all_passed:
    print("*** ALL VERIFICATIONS PASSED ***")
    print("The exclusion was performed 100% CORRECTLY")
    print(f"\nFinal counts confirmed:")
    print(f"  - Original: {len(original)} transactions")
    print(f"  - Excluded: {len(verified_ids)} verified duplicates")
    print(f"  - Remaining: {len(filtered)} unanalyzed transactions")
else:
    print("*** VERIFICATION FAILED ***")
    print("CRITICAL: The exclusion has errors that need investigation")
    failed_checks = [name for name, passed in verification_results if not passed]
    print(f"Failed checks: {', '.join(failed_checks)}")
print("=" * 80)