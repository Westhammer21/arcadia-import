#!/usr/bin/env python3
"""Verify that only arc_hq_country was changed for TO BE CREATED records"""

import pandas as pd

# Compare original backup with current file
print("Comparing backup with current file to verify only arc_hq_country changed...")

# Read both files
backup_file = "archive/ig_arc_unmapped_FINAL_COMPLETE_BACKUP_20250904_164230.csv"
current_file = "output/ig_arc_unmapped_FINAL_COMPLETE.csv"

df_backup = pd.read_csv(backup_file, dtype=str, na_filter=False)
df_current = pd.read_csv(current_file, dtype=str, na_filter=False)

# Check if same number of rows
print(f"Backup rows: {len(df_backup)}")
print(f"Current rows: {len(df_current)}")

if len(df_backup) != len(df_current):
    print("ERROR: Different number of rows!")
    exit(1)

# Compare all columns except arc_hq_country
columns_to_check = [col for col in df_backup.columns if col != 'arc_hq_country']
other_changes = []

for idx in range(len(df_backup)):
    for col in columns_to_check:
        if df_backup.at[idx, col] != df_current.at[idx, col]:
            other_changes.append({
                'row': idx + 2,
                'column': col,
                'old_value': df_backup.at[idx, col],
                'new_value': df_current.at[idx, col]
            })

if other_changes:
    print(f"\nWARNING: Found {len(other_changes)} changes in other columns:")
    for change in other_changes[:10]:  # Show first 10
        print(f"  Row {change['row']}, Column {change['column']}:")
        print(f"    Old: '{change['old_value']}'")
        print(f"    New: '{change['new_value']}'")
else:
    print("\n[OK] VERIFIED: No changes to any other columns besides arc_hq_country")

# Now check arc_hq_country changes for TO BE CREATED records
print("\n" + "="*60)
print("Arc_hq_country changes for TO BE CREATED records:")
print("="*60)

to_be_created_mask = df_backup['arc_id'] == 'TO BE CREATED'
changes_count = 0

for idx in df_backup[to_be_created_mask].index:
    old_val = df_backup.at[idx, 'arc_hq_country']
    new_val = df_current.at[idx, 'arc_hq_country']
    
    if old_val != new_val:
        changes_count += 1
        if changes_count <= 10:  # Show first 10 changes
            target_name = df_backup.at[idx, 'Target name']
            print(f"Row {idx+2}: {target_name}")
            print(f"  Changed: '{old_val}' -> '{new_val}'")

print(f"\nTotal arc_hq_country changes for TO BE CREATED records: {changes_count}")

# Check for records that were NOT 'TO BE CREATED' 
non_to_be_created_changes = 0
for idx in range(len(df_backup)):
    if df_backup.at[idx, 'arc_id'] != 'TO BE CREATED':
        if df_backup.at[idx, 'arc_hq_country'] != df_current.at[idx, 'arc_hq_country']:
            non_to_be_created_changes += 1
            if non_to_be_created_changes <= 5:
                print(f"WARNING: Non-TO BE CREATED record changed at row {idx+2}")

if non_to_be_created_changes == 0:
    print("\n[OK] VERIFIED: No arc_hq_country changes to non-'TO BE CREATED' records")
else:
    print(f"\n[ERROR]: {non_to_be_created_changes} non-'TO BE CREATED' records were modified!")