import pandas as pd
import numpy as np
import random

# File paths
new_mapping_file = 'output/arc_new_human_checked.csv'
current_full_file = 'output/ig_arc_mapping_full.csv'
arcadia_db_file = 'src/arcadia_database_2025-09-01.csv'
output_file = 'output/ig_arc_mapping_full.csv'  # Overwrite existing

print("=" * 80)
print("APPLYING NEW MAPPINGS TO ENRICH DATA")
print("=" * 80)

# 1. Read the new mapping file
print("\n1. Reading new mapping file (arc_new_human_checked.csv)...")
df_new_mapping = pd.read_csv(new_mapping_file, encoding='utf-8-sig')

# Filter for valid numeric IG_ID_MAP values only
ig_id_map_values = df_new_mapping['IG_ID_MAP'].dropna()
numeric_mask = ig_id_map_values.astype(str).str.isdigit()
valid_new_mappings = df_new_mapping[df_new_mapping['IG_ID_MAP'].notna() & 
                                   df_new_mapping['IG_ID_MAP'].astype(str).str.isdigit()].copy()

# Convert IG_ID_MAP to integer for valid mappings
valid_new_mappings['IG_ID_MAP'] = valid_new_mappings['IG_ID_MAP'].astype(int)

print(f"   Total records in new mapping: {len(df_new_mapping)}")
print(f"   Valid numeric mappings: {len(valid_new_mappings)}")
print(f"   Ignored non-numeric (OLD, etc.): {len(df_new_mapping) - len(valid_new_mappings) - df_new_mapping['IG_ID_MAP'].isna().sum()}")

# 2. Read current full mapping
print("\n2. Reading current full mapping (ig_arc_mapping_full.csv)...")
df_current = pd.read_csv(current_full_file)
print(f"   Loaded {len(df_current)} records")

# Check current mapping status
currently_mapped = len(df_current[df_current['ARCADIA_TR_ID'].notna() & (df_current['ARCADIA_TR_ID'] != '')])
print(f"   Currently mapped: {currently_mapped}")

# 3. Read Arcadia database for enrichment
print("\n3. Reading Arcadia database...")
df_arcadia = pd.read_csv(arcadia_db_file, sep='\t')
print(f"   Loaded {len(df_arcadia)} Arcadia transactions")

# Rename Arcadia columns with ARC_ prefix
arcadia_renamed = {}
for col in df_arcadia.columns:
    if col == 'ID':
        arcadia_renamed[col] = 'ARC_ID_TEMP'  # Temporary name for merging
    else:
        arcadia_renamed[col] = f'ARC_{col}'

df_arcadia_renamed = df_arcadia.rename(columns=arcadia_renamed)

# 4. Apply new mappings
print("\n4. Applying new mappings...")

# Create a mapping dictionary from new mappings
new_mapping_dict = dict(zip(valid_new_mappings['IG_ID_MAP'], valid_new_mappings['ID']))

# Track which records will be updated
records_to_update = []
for ig_id, arc_id in new_mapping_dict.items():
    # Check if this IG_ID exists and is currently unmapped
    mask = (df_current['IG_ID'] == ig_id) & \
           ((df_current['ARCADIA_TR_ID'].isna()) | (df_current['ARCADIA_TR_ID'] == ''))
    
    if mask.any():
        records_to_update.append((ig_id, arc_id))
        # Update ARCADIA_TR_ID
        df_current.loc[mask, 'ARCADIA_TR_ID'] = str(arc_id)
        # Also update ARCADIA_TR_URL
        df_current.loc[mask, 'ARCADIA_TR_URL'] = f'https://arcadia.investgame.net/admin/transactions/transaction/{arc_id}/change/'

print(f"   Applied {len(records_to_update)} new mappings")

# 5. Enrich with Arcadia data for newly mapped records
print("\n5. Enriching newly mapped records with Arcadia data...")

# Get list of new Arcadia IDs to fetch
new_arc_ids = [arc_id for _, arc_id in records_to_update]

# Filter Arcadia data for these IDs
df_arcadia_subset = df_arcadia_renamed[df_arcadia_renamed['ARC_ID_TEMP'].isin(new_arc_ids)].copy()
print(f"   Found {len(df_arcadia_subset)} Arcadia records for enrichment")

# Update ARC_ columns for newly mapped records
enriched_count = 0
for ig_id, arc_id in records_to_update:
    # Find the row in current data
    current_mask = df_current['IG_ID'] == ig_id
    
    # Find the Arcadia data
    arcadia_mask = df_arcadia_subset['ARC_ID_TEMP'] == arc_id
    
    if current_mask.any() and arcadia_mask.any():
        # Get Arcadia data
        arcadia_row = df_arcadia_subset[arcadia_mask].iloc[0]
        
        # Update all ARC_ columns
        for col in df_arcadia_subset.columns:
            if col == 'ARC_ID_TEMP':
                # Map to ARC_ID column
                df_current.loc[current_mask, 'ARC_ID'] = arcadia_row[col]
            elif col in df_current.columns:
                df_current.loc[current_mask, col] = arcadia_row[col]
        
        enriched_count += 1

print(f"   Enriched {enriched_count} records with Arcadia data")

# 6. Statistics
print("\n6. ENRICHMENT STATISTICS:")
new_mapped_count = len(df_current[df_current['ARCADIA_TR_ID'].notna() & (df_current['ARCADIA_TR_ID'] != '')])
new_enriched_count = len(df_current[df_current['ARC_ID'].notna()])

print(f"   Total records: {len(df_current)}")
print(f"   Previously mapped: {currently_mapped}")
print(f"   Now mapped: {new_mapped_count}")
print(f"   New mappings added: {new_mapped_count - currently_mapped}")
print(f"   Records with Arcadia enrichment: {new_enriched_count}")

# 7. Perform 100 random validation checks on newly mapped records
print("\n7. PERFORMING 100 RANDOM VALIDATION CHECKS...")
print("=" * 60)

# Get newly mapped records for validation
newly_mapped_ig_ids = [ig_id for ig_id, _ in records_to_update]
newly_mapped_records = df_current[df_current['IG_ID'].isin(newly_mapped_ig_ids)]

# Sample for validation (up to 100)
sample_size = min(100, len(newly_mapped_records))
if sample_size > 0:
    sample_records = newly_mapped_records.sample(sample_size, random_state=42)
    
    validation_results = []
    all_match = True
    
    print(f"Checking {sample_size} newly mapped records...")
    
    for idx, row in sample_records.iterrows():
        ig_id = row['IG_ID']
        arcadia_id = row['ARCADIA_TR_ID']
        arc_id = row['ARC_ID'] if 'ARC_ID' in row else None
        
        # Check if IDs match
        if pd.notna(arc_id) and pd.notna(arcadia_id):
            try:
                id_match = int(float(arcadia_id)) == int(float(arc_id))
            except:
                id_match = False
        else:
            id_match = False
        
        # Get target names
        ig_target = row['Target name']
        arc_target = row['ARC_Target Company'] if 'ARC_Target Company' in row else None
        
        validation_results.append({
            'IG_ID': ig_id,
            'ARCADIA_TR_ID': arcadia_id,
            'ARC_ID': arc_id,
            'ID_Match': id_match,
            'IG_Target': ig_target,
            'ARC_Target': arc_target
        })
        
        if not id_match:
            all_match = False
    
    # Display first 10 validation results
    print("\nSample validation results (first 10):")
    for i, result in enumerate(validation_results[:10]):
        print(f"\n   Check #{i+1}:")
        print(f"   IG_ID: {result['IG_ID']}")
        print(f"   ARCADIA_TR_ID: {result['ARCADIA_TR_ID']} -> ARC_ID: {result['ARC_ID']}")
        print(f"   ID Match: {'[OK]' if result['ID_Match'] else '[MISMATCH]'}")
        print(f"   IG Target: {result['IG_Target']}")
        print(f"   ARC Target: {result['ARC_Target']}")
    
    # Summary
    valid_count = sum(1 for r in validation_results if r['ID_Match'])
    print(f"\n   VALIDATION SUMMARY:")
    print(f"   Total checked: {len(validation_results)}")
    print(f"   ID matches: {valid_count} ({valid_count/len(validation_results)*100:.1f}%)")

# 8. Save the updated file
print("\n8. Saving updated file...")
df_current.to_csv(output_file, index=False)
print(f"   Saved to: {output_file} (overwritten)")

# 9. Final report
print("\n9. FINAL REPORT:")
print("=" * 60)
print(f"   Input records: {len(df_current)}")
print(f"   New mappings applied: {len(records_to_update)}")
print(f"   Total mapped records: {new_mapped_count}")
print(f"   Total unmapped records: {len(df_current) - new_mapped_count}")
print(f"   Coverage: {new_mapped_count/len(df_current)*100:.1f}%")
print(f"   Records with full Arcadia data: {new_enriched_count}")

# Check for any issues
duplicate_check = df_current[df_current.duplicated(['IG_ID'], keep=False)]
print(f"   Duplicate IG_IDs: {len(duplicate_check)} {'[OK]' if len(duplicate_check) == 0 else '[WARNING]'}")

print("\n" + "=" * 80)
print("NEW MAPPINGS APPLIED SUCCESSFULLY!")
print("=" * 80)