import pandas as pd

# Read both files
investgame_file = 'output/investgame_database_clean_with_IG_ID.csv'
mapping_file = 'output/human_verified_duplicates.csv'

# Read the files
df_investgame = pd.read_csv(investgame_file)
df_mapping = pd.read_csv(mapping_file, sep='\t')  # Tab-delimited file

print("=" * 80)
print("DATA VERIFICATION REPORT")
print("=" * 80)

# 1. Check InvestGame database
print("\n1. INVESTGAME DATABASE:")
print(f"   Total rows: {len(df_investgame)}")
print(f"   Columns: {list(df_investgame.columns)}")
print(f"   IG_ID range: {df_investgame['IG_ID'].min()} to {df_investgame['IG_ID'].max()}")
print(f"   IG_ID data type: {df_investgame['IG_ID'].dtype}")

# 2. Check mapping file
print("\n2. MAPPING FILE (human_verified_duplicates.csv):")
print(f"   Total mapping rows: {len(df_mapping)}")
print(f"   Columns: {list(df_mapping.columns)}")
print(f"   ig_id range: {df_mapping['ig_id'].min()} to {df_mapping['ig_id'].max()}")
print(f"   ig_id data type: {df_mapping['ig_id'].dtype}")

# 3. Check for duplicates in mapping
print("\n3. MAPPING INTEGRITY:")
duplicate_ig_ids = df_mapping[df_mapping.duplicated(['ig_id'], keep=False)]
print(f"   Duplicate ig_ids in mapping: {len(duplicate_ig_ids)}")
if len(duplicate_ig_ids) > 0:
    print(f"   Duplicate ig_ids: {duplicate_ig_ids['ig_id'].unique()[:10]}")

# 4. Check how many InvestGame records have mapping
mapped_ig_ids = set(df_mapping['ig_id'].values)
investgame_ig_ids = set(df_investgame['IG_ID'].values)
matched_ids = mapped_ig_ids.intersection(investgame_ig_ids)

print("\n4. MAPPING COVERAGE:")
print(f"   InvestGame records: {len(investgame_ig_ids)}")
print(f"   Mapping records: {len(mapped_ig_ids)}")
print(f"   Matched records: {len(matched_ids)}")
print(f"   Coverage: {len(matched_ids)/len(investgame_ig_ids)*100:.1f}%")

# 5. Check for mapping IDs not in InvestGame
orphan_mappings = mapped_ig_ids - investgame_ig_ids
print(f"   Mapping IDs not in InvestGame: {len(orphan_mappings)}")
if len(orphan_mappings) > 0 and len(orphan_mappings) <= 10:
    print(f"   Orphan IDs: {sorted(orphan_mappings)[:10]}")

# 6. Sample mapping data
print("\n5. SAMPLE MAPPING DATA (first 5 rows):")
print("   ig_id -> A_TR_ID (ARCADIA_TR_ID)")
for idx, row in df_mapping.head().iterrows():
    print(f"   {row['ig_id']} -> {row['A_TR_ID']}")

print("\n" + "=" * 80)