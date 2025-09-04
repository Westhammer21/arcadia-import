"""
Randomly verify 100 IDs between investgame_database_clean_with_IG_ID.csv 
and Correct Transaction Imported.csv
"""
import pandas as pd
import random

print("=" * 70)
print("RANDOM VERIFICATION OF 100 IG_ID MAPPINGS")
print("=" * 70)

# 1. Load both databases
print("\n1. LOADING DATABASES...")
ig_db = pd.read_csv('src/investgame_database_clean_with_IG_ID.csv')
print(f"   InvestGame database: {len(ig_db)} rows")

# Load verified duplicates (tab-delimited)
verified = pd.read_csv('output/Correct Transaction Imported.csv', sep='\t', encoding='utf-8')
print(f"   Verified duplicates: {len(verified)} rows")

# Clean the Cyrillic character issue we found earlier
verified['ig_target_clean'] = verified['ig_target'].str.replace('В', '').str.strip()

# 2. Get random sample of 100 IDs from verified duplicates
print("\n2. SELECTING RANDOM 100 IDS...")
available_ids = verified['ig_id'].dropna().unique()
print(f"   Available IDs in verified file: {len(available_ids)}")

# Take random sample
random.seed(42)  # For reproducibility
sample_size = min(100, len(available_ids))
random_ids = random.sample(list(available_ids), sample_size)
random_ids.sort()
print(f"   Selected {sample_size} random IDs for verification")

# 3. Verify each ID
print("\n3. VERIFYING MAPPINGS...")
matches = []
mismatches = []

for ig_id in random_ids:
    ig_id_int = int(ig_id)
    
    # Get from InvestGame database using IG_ID column
    if ig_id_int in ig_db['IG_ID'].values:
        ig_row = ig_db[ig_db['IG_ID'] == ig_id_int].iloc[0]
        ig_target = ig_row['Target name'].strip()
        
        # Get from verified file
        ver_row = verified[verified['ig_id'] == ig_id].iloc[0]
        ver_target = ver_row['ig_target_clean'].strip()
        
        # Compare
        if ig_target == ver_target:
            matches.append({
                'ig_id': ig_id_int,
                'target': ig_target
            })
        else:
            mismatches.append({
                'ig_id': ig_id_int,
                'ig_target': ig_target,
                'ver_target': ver_target
            })
    else:
        mismatches.append({
            'ig_id': ig_id_int,
            'ig_target': 'NOT FOUND IN IG_DB',
            'ver_target': verified[verified['ig_id'] == ig_id].iloc[0]['ig_target_clean']
        })

# 4. Report results
print(f"\n4. RESULTS FOR {len(random_ids)} RANDOM IDS:")
print(f"   SUCCESS Matches: {len(matches)}")
print(f"   ERROR Mismatches: {len(mismatches)}")
print(f"   Accuracy: {len(matches)/len(random_ids)*100:.1f}%")

# Show sample of matches
if matches:
    print(f"\n   Sample MATCHES (first 10):")
    for match in matches[:10]:
        print(f"   ID {match['ig_id']:4} -> '{match['target']}'")

# Show ALL mismatches (should be 0)
if mismatches:
    print(f"\n   MISMATCHES FOUND (CRITICAL):")
    for mm in mismatches:
        print(f"   ID {mm['ig_id']:4}")
        print(f"     IG DB: '{mm['ig_target']}'")
        print(f"     Verified: '{mm['ver_target']}'")
else:
    print("\n   SUCCESS: NO MISMATCHES - Perfect mapping!")

# 5. Show distribution of sampled IDs
print(f"\n5. DISTRIBUTION OF SAMPLED IDS:")
print(f"   Min ID: {min(random_ids)}")
print(f"   Max ID: {max(random_ids)}")
print(f"   Median ID: {sorted(random_ids)[len(random_ids)//2]}")

# Show some specific examples from different ranges
print(f"\n   Examples from different ranges:")
ranges = [(0, 1000), (1000, 2000), (2000, 3000), (3000, 4000)]
for start, end in ranges:
    ids_in_range = [id for id in random_ids if start <= id < end]
    if ids_in_range:
        sample_id = ids_in_range[0]
        target = ig_db[ig_db['IG_ID'] == sample_id]['Target name'].iloc[0]
        print(f"   ID {sample_id:4} (range {start}-{end}): '{target}'")

# 6. Save detailed results
print("\n6. SAVING DETAILED RESULTS...")
results_df = pd.DataFrame({
    'ig_id': random_ids,
    'ig_target': [ig_db[ig_db['IG_ID'] == id]['Target name'].iloc[0] if id in ig_db['IG_ID'].values else 'NOT FOUND' for id in random_ids],
    'ver_target': [verified[verified['ig_id'] == id]['ig_target_clean'].iloc[0] for id in random_ids],
    'match': [ig_db[ig_db['IG_ID'] == id]['Target name'].iloc[0].strip() == verified[verified['ig_id'] == id]['ig_target_clean'].iloc[0].strip() if id in ig_db['IG_ID'].values else False for id in random_ids]
})

results_df.to_csv('output/random_100_verification_results.csv', index=False)
print(f"   Saved to output/random_100_verification_results.csv")

# Summary
print("\n" + "=" * 70)
if len(mismatches) == 0:
    print("VERIFICATION SUCCESSFUL - 100% ACCURACY ON RANDOM SAMPLE")
    print(f"All {len(random_ids)} randomly selected IDs mapped perfectly!")
else:
    print(f"VERIFICATION FAILED - Found {len(mismatches)} mismatches")
    print("Please investigate the mismatches above")
print("=" * 70)