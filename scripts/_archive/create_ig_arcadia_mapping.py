import pandas as pd
import numpy as np

# File paths
investgame_file = 'output/investgame_database_clean_with_IG_ID.csv'
mapping_file = 'output/human_verified_duplicates.csv'
output_file = 'output/ig_arcadia_mapping.csv'

print("=" * 80)
print("CREATING IG-ARCADIA MAPPING TABLE")
print("=" * 80)

# 1. Read the InvestGame database
print("\n1. Reading InvestGame database...")
df_investgame = pd.read_csv(investgame_file)
print(f"   Loaded {len(df_investgame)} transactions")
print(f"   Columns: {len(df_investgame.columns)}")

# 2. Read the mapping file (tab-delimited)
print("\n2. Reading mapping file...")
df_mapping = pd.read_csv(mapping_file, sep='\t')
print(f"   Loaded {len(df_mapping)} mappings")

# 3. Select only needed columns from mapping
print("\n3. Preparing mapping data...")
df_mapping_clean = df_mapping[['ig_id', 'A_TR_ID', 'A_TR_URL']].copy()
# Rename columns for clarity
df_mapping_clean.columns = ['IG_ID', 'ARCADIA_TR_ID', 'ARCADIA_TR_URL']
print(f"   Selected columns: IG_ID -> ARCADIA_TR_ID, ARCADIA_TR_URL")

# 4. Perform left join
print("\n4. Performing left join on IG_ID...")
df_result = pd.merge(
    df_investgame,
    df_mapping_clean,
    on='IG_ID',
    how='left'
)
print(f"   Result: {len(df_result)} rows")

# 5. Handle unmapped records (replace NaN with empty strings)
print("\n5. Handling unmapped records...")
df_result['ARCADIA_TR_ID'] = df_result['ARCADIA_TR_ID'].fillna('')
df_result['ARCADIA_TR_URL'] = df_result['ARCADIA_TR_URL'].fillna('')

# Convert ARCADIA_TR_ID to integer where possible, keep as string
def convert_id(val):
    if val == '':
        return ''
    try:
        return str(int(float(val)))
    except:
        return str(val)

df_result['ARCADIA_TR_ID'] = df_result['ARCADIA_TR_ID'].apply(convert_id)

# 6. Statistics
mapped_count = len(df_result[df_result['ARCADIA_TR_ID'] != ''])
unmapped_count = len(df_result[df_result['ARCADIA_TR_ID'] == ''])

print("\n6. MAPPING STATISTICS:")
print(f"   Total records: {len(df_result)}")
print(f"   Mapped records: {mapped_count} ({mapped_count/len(df_result)*100:.1f}%)")
print(f"   Unmapped records: {unmapped_count} ({unmapped_count/len(df_result)*100:.1f}%)")

# 7. Random verification checks
print("\n7. RANDOM VERIFICATION CHECKS (10 samples):")
print("-" * 60)

# Get 10 random mapped records for verification
mapped_records = df_result[df_result['ARCADIA_TR_ID'] != ''].sample(min(10, mapped_count), random_state=42)

for idx, row in mapped_records.iterrows():
    ig_id = row['IG_ID']
    target = row['Target name']
    arcadia_id = row['ARCADIA_TR_ID']
    
    # Find original mapping
    orig_map = df_mapping[df_mapping['ig_id'] == ig_id]
    if not orig_map.empty:
        orig_arcadia_id = orig_map.iloc[0]['A_TR_ID']
        orig_target = orig_map.iloc[0]['ig_target']
        match_status = "[MATCH]" if str(orig_arcadia_id) == str(arcadia_id) else "[MISMATCH]"
        
        print(f"   IG_ID: {ig_id}")
        print(f"   Target: {target}")
        print(f"   Mapped ARCADIA_TR_ID: {arcadia_id}")
        print(f"   Original A_TR_ID: {orig_arcadia_id} - {match_status}")
        print("-" * 60)

# 8. Save the result
print("\n8. Saving output file...")
df_result.to_csv(output_file, index=False)
print(f"   Saved to: {output_file}")

# 9. Final validation
print("\n9. FINAL VALIDATION:")
print(f"   Output columns: {list(df_result.columns)}")
print(f"   ARCADIA columns at end: {list(df_result.columns[-2:])}")
print(f"   Total rows preserved: {len(df_result) == len(df_investgame)}")

print("\n" + "=" * 80)
print("MAPPING TABLE CREATED SUCCESSFULLY!")
print("=" * 80)