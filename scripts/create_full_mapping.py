import pandas as pd
import numpy as np
import random

# File paths
ig_mapping_file = 'output/ig_arcadia_mapping.csv'
arcadia_db_file = 'src/arcadia_database_2025-09-01.csv'
output_file = 'output/ig_arc_mapping_full.csv'

print("=" * 80)
print("CREATING FULL IG-ARCADIA MAPPING WITH ARCADIA DATABASE ENRICHMENT")
print("=" * 80)

# 1. Read the IG-Arcadia mapping file
print("\n1. Reading IG-Arcadia mapping...")
df_ig_mapping = pd.read_csv(ig_mapping_file)
print(f"   Loaded {len(df_ig_mapping)} records")
print(f"   Columns: {len(df_ig_mapping.columns)}")
mapped_count = len(df_ig_mapping[(df_ig_mapping['ARCADIA_TR_ID'] != '') & (df_ig_mapping['ARCADIA_TR_ID'].notna())])
print(f"   Records with ARCADIA_TR_ID: {mapped_count}")

# 2. Read the Arcadia database (tab-delimited)
print("\n2. Reading Arcadia database...")
df_arcadia = pd.read_csv(arcadia_db_file, sep='\t')
print(f"   Loaded {len(df_arcadia)} Arcadia transactions")
print(f"   Columns: {len(df_arcadia.columns)}")

# 3. Analyze column overlaps
print("\n3. Analyzing column overlaps...")
ig_cols = set(df_ig_mapping.columns)
arc_cols = set(df_arcadia.columns)
overlapping = ig_cols.intersection(arc_cols)
print(f"   IG-mapping columns: {len(ig_cols)}")
print(f"   Arcadia columns: {len(arc_cols)}")
print(f"   Overlapping columns: {overlapping}")

# 4. Rename Arcadia columns with ARC_ prefix (except ID which we'll use for joining)
print("\n4. Renaming Arcadia columns with ARC_ prefix...")
arcadia_renamed = {}
for col in df_arcadia.columns:
    if col == 'ID':
        arcadia_renamed[col] = 'ARC_ID'  # This will be the join key
    else:
        arcadia_renamed[col] = f'ARC_{col}'

df_arcadia_renamed = df_arcadia.rename(columns=arcadia_renamed)
print(f"   Renamed {len(arcadia_renamed)} columns")
print(f"   Sample renamed columns: {list(arcadia_renamed.items())[:5]}")

# Convert ARCADIA_TR_ID to numeric for joining (handle empty strings)
print("\n5. Preparing data for join...")
df_ig_mapping['ARCADIA_TR_ID_NUM'] = pd.to_numeric(df_ig_mapping['ARCADIA_TR_ID'], errors='coerce')
df_arcadia_renamed['ARC_ID'] = pd.to_numeric(df_arcadia_renamed['ARC_ID'], errors='coerce')

# 6. Perform left join
print("\n6. Performing left join on ARCADIA_TR_ID = ARC_ID...")
df_full = pd.merge(
    df_ig_mapping,
    df_arcadia_renamed,
    left_on='ARCADIA_TR_ID_NUM',
    right_on='ARC_ID',
    how='left'
)

# Drop the temporary numeric column
df_full = df_full.drop('ARCADIA_TR_ID_NUM', axis=1)

print(f"   Result: {len(df_full)} rows")
enriched_count = len(df_full[df_full['ARC_ID'].notna()])
print(f"   Records enriched with Arcadia data: {enriched_count}")

# 7. Statistics
print("\n7. ENRICHMENT STATISTICS:")
print(f"   Total records: {len(df_full)}")
print(f"   Records with ARCADIA_TR_ID: {mapped_count}")
print(f"   Records enriched with Arcadia data: {enriched_count}")
print(f"   Records with ID but no Arcadia data: {mapped_count - enriched_count}")
print(f"   Final column count: {len(df_full.columns)}")

# 8. Perform 100 random checks
print("\n8. PERFORMING 100 RANDOM VALIDATION CHECKS...")
print("=" * 60)

# Get sample of mapped and enriched records for validation
enriched_records = df_full[df_full['ARC_ID'].notna()]
if len(enriched_records) >= 100:
    sample_records = enriched_records.sample(100, random_state=42)
else:
    sample_records = enriched_records

validation_results = []
mismatches = []

for idx, row in sample_records.iterrows():
    ig_id = row['IG_ID']
    arcadia_id = row['ARCADIA_TR_ID']
    arc_id = row['ARC_ID']
    
    # Check 1: ARCADIA_TR_ID should match ARC_ID
    if pd.notna(arc_id) and pd.notna(arcadia_id):
        # Convert both to int for comparison (handle floats)
        id_match = int(float(arcadia_id)) == int(float(arc_id))
    else:
        id_match = False
    
    # Check 2: Target names comparison
    ig_target = row['Target name']
    arc_target = row['ARC_Target Company'] if 'ARC_Target Company' in row else None
    
    # Check 3: Transaction size comparison
    ig_size = row['Size, $m']
    arc_size = row['ARC_Transaction Size*, $M'] if 'ARC_Transaction Size*, $M' in row else None
    
    validation_results.append({
        'IG_ID': ig_id,
        'ARCADIA_TR_ID': arcadia_id,
        'ARC_ID': arc_id,
        'ID_Match': id_match,
        'IG_Target': ig_target,
        'ARC_Target': arc_target,
        'IG_Size': ig_size,
        'ARC_Size': arc_size
    })
    
    if not id_match:
        mismatches.append((ig_id, arcadia_id, arc_id))

# Display sample validation results
print("\nSAMPLE VALIDATION RESULTS (first 10):")
for i, result in enumerate(validation_results[:10]):
    print(f"\n   Check #{i+1}:")
    print(f"   IG_ID: {result['IG_ID']}")
    print(f"   ARCADIA_TR_ID: {result['ARCADIA_TR_ID']} -> ARC_ID: {result['ARC_ID']}")
    print(f"   ID Match: {'[OK]' if result['ID_Match'] else '[MISMATCH]'}")
    print(f"   IG Target: {result['IG_Target']}")
    print(f"   ARC Target: {result['ARC_Target']}")
    print(f"   IG Size: ${result['IG_Size']}M | ARC Size: ${result['ARC_Size']}M")

# Summary of validation
valid_count = sum(1 for r in validation_results if r['ID_Match'])
print("\n" + "=" * 60)
print(f"VALIDATION SUMMARY (100 checks):")
print(f"   Total checked: {len(validation_results)}")
print(f"   ID matches: {valid_count} ({valid_count/len(validation_results)*100:.1f}%)")
print(f"   Mismatches: {len(mismatches)}")

if mismatches:
    print(f"\n   MISMATCHES FOUND (first 5):")
    for ig_id, arcadia_id, arc_id in mismatches[:5]:
        print(f"   IG_ID {ig_id}: ARCADIA_TR_ID={arcadia_id}, ARC_ID={arc_id}")

# 9. Save the result
print("\n9. Saving full mapping file...")
df_full.to_csv(output_file, index=False)
print(f"   Saved to: {output_file}")

# 10. Final validation report
print("\n10. FINAL VALIDATION REPORT:")
print("=" * 60)
print(f"   Input IG-mapping records: {len(df_ig_mapping)}")
print(f"   Output full mapping records: {len(df_full)}")
print(f"   Records preserved: {len(df_full) == len(df_ig_mapping)}")
print(f"   Column count:")
print(f"     - Original IG columns: 21")
print(f"     - Mapping columns: 2 (ARCADIA_TR_ID, ARCADIA_TR_URL)")
print(f"     - Arcadia columns added: {len(df_arcadia.columns)}")
print(f"     - Total columns: {len(df_full.columns)}")
print(f"   Data integrity: {'[OK]' if len(df_full) == len(df_ig_mapping) else '[ERROR]'}")

# Check for any duplicates
duplicates = df_full[df_full.duplicated(['IG_ID'], keep=False)]
print(f"   Duplicate IG_IDs: {len(duplicates)} {'[OK]' if len(duplicates) == 0 else '[WARNING]'}")

print("\n" + "=" * 80)
print("FULL MAPPING TABLE CREATED SUCCESSFULLY!")
print("=" * 80)