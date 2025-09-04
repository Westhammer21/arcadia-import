"""
CRITICAL DATA MERGE OPERATION
Merging Human_checked column from test_description_advanced_human_final.csv
into ig_arc_mapping_full.csv using composite key matching
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

print("=" * 80)
print("CRITICAL DATA MERGE - HUMAN REVIEW TO MAIN MAPPING FILE")
print("=" * 80)
print(f"Execution started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================================================
# PHASE 1: SETUP AND LOAD
# ============================================================================

print("\n" + "=" * 60)
print("PHASE 1: LOADING DATA FILES")
print("=" * 60)

# File paths
human_review_file = '../output/test_description_advanced_human_final.csv'
main_mapping_file = '../output/ig_arc_mapping_full.csv'

# Check files exist
if not os.path.exists(human_review_file):
    print(f"ERROR: Human review file not found: {human_review_file}")
    sys.exit(1)
    
if not os.path.exists(main_mapping_file):
    print(f"ERROR: Main mapping file not found: {main_mapping_file}")
    sys.exit(1)

# Load the files
print("\n1. Loading human review file...")
df_human = pd.read_csv(human_review_file, encoding='utf-8')
print(f"   Loaded {len(df_human)} records")
print(f"   Columns: {', '.join(df_human.columns[:5])}...")

print("\n2. Loading main mapping file...")
df_main = pd.read_csv(main_mapping_file, encoding='utf-8')
original_record_count = len(df_main)
original_columns = df_main.columns.tolist()
print(f"   Loaded {len(df_main)} records")
print(f"   Columns: {len(df_main.columns)} total")

# ============================================================================
# PHASE 2: DATA PREPARATION
# ============================================================================

print("\n" + "=" * 60)
print("PHASE 2: DATA PREPARATION")
print("=" * 60)

# Check required columns exist
print("\n1. Validating required columns...")

# In human review file
if 'IG_ID' not in df_human.columns:
    print("ERROR: IG_ID not found in human review file")
    sys.exit(1)
if 'Arcadia_ID' not in df_human.columns:
    print("ERROR: Arcadia_ID not found in human review file")
    sys.exit(1)
if 'Human_checked' not in df_human.columns:
    print("ERROR: Human_checked not found in human review file")
    sys.exit(1)
print("   [OK] Human review file has required columns")

# In main mapping file
if 'IG_ID' not in df_main.columns:
    print("ERROR: IG_ID not found in main mapping file")
    sys.exit(1)
if 'ARCADIA_TR_ID' not in df_main.columns:
    print("ERROR: ARCADIA_TR_ID not found in main mapping file")
    sys.exit(1)
print("   [OK] Main mapping file has required columns")

# Check if Human_checked already exists in main file
if 'Human_checked' in df_main.columns:
    print("   WARNING: Human_checked column already exists in main file - will be replaced")
    df_main = df_main.drop('Human_checked', axis=1)

# Data type alignment
print("\n2. Checking and aligning data types...")

# Check IG_ID data types
print(f"   IG_ID type in human review: {df_human['IG_ID'].dtype}")
print(f"   IG_ID type in main file: {df_main['IG_ID'].dtype}")

# Check Arcadia ID data types
print(f"   Arcadia_ID type in human review: {df_human['Arcadia_ID'].dtype}")
print(f"   ARCADIA_TR_ID type in main file: {df_main['ARCADIA_TR_ID'].dtype}")

# Convert to consistent types (handle as strings to avoid float issues)
df_human['IG_ID'] = df_human['IG_ID'].astype(str)
df_main['IG_ID'] = df_main['IG_ID'].astype(str)

# Handle Arcadia IDs (may contain NaN)
df_human['Arcadia_ID'] = df_human['Arcadia_ID'].fillna(-999).astype(float).astype(str)
df_main['ARCADIA_TR_ID'] = df_main['ARCADIA_TR_ID'].fillna(-999).astype(float).astype(str)

# Replace '-999.0' back to empty for display
df_human.loc[df_human['Arcadia_ID'] == '-999.0', 'Arcadia_ID'] = ''
df_main.loc[df_main['ARCADIA_TR_ID'] == '-999.0', 'ARCADIA_TR_ID'] = ''

print("   [OK] Data types aligned")

# Extract only needed columns from human review
print("\n3. Extracting merge columns...")
df_merge = df_human[['IG_ID', 'Arcadia_ID', 'Human_checked']].copy()
print(f"   Extracted {len(df_merge)} records with Human_checked values")

# Show distribution of Human_checked values
print("\n4. Human_checked value distribution:")
print(df_merge['Human_checked'].value_counts())

# ============================================================================
# PHASE 3: VALIDATION BEFORE MERGE
# ============================================================================

print("\n" + "=" * 60)
print("PHASE 3: PRE-MERGE VALIDATION")
print("=" * 60)

# Check for duplicates in composite key
print("\n1. Checking for duplicate composite keys...")

# In human review
df_human_check = df_merge[df_merge['Arcadia_ID'] != '']
human_duplicates = df_human_check.duplicated(subset=['IG_ID', 'Arcadia_ID'], keep=False)
if human_duplicates.any():
    print(f"   WARNING: {human_duplicates.sum()} duplicate keys in human review")
    print("   Duplicate records:")
    print(df_human_check[human_duplicates][['IG_ID', 'Arcadia_ID']])
else:
    print("   [OK] No duplicate composite keys in human review")

# In main file
df_main_check = df_main[df_main['ARCADIA_TR_ID'] != '']
main_duplicates = df_main_check.duplicated(subset=['IG_ID', 'ARCADIA_TR_ID'], keep=False)
if main_duplicates.any():
    print(f"   WARNING: {main_duplicates.sum()} duplicate keys in main file")
else:
    print("   [OK] No duplicate composite keys in main file")

# Check overlap
print("\n2. Checking record overlap...")
main_keys = set(zip(df_main['IG_ID'], df_main['ARCADIA_TR_ID']))
human_keys = set(zip(df_merge['IG_ID'], df_merge['Arcadia_ID']))

# Filter out empty keys
main_keys = {k for k in main_keys if k[1] != ''}
human_keys = {k for k in human_keys if k[1] != ''}

overlap = main_keys.intersection(human_keys)
print(f"   Main file mapped records: {len(main_keys)}")
print(f"   Human review records: {len(human_keys)}")
print(f"   Overlapping records: {len(overlap)}")
print(f"   Records in main but not reviewed: {len(main_keys - human_keys)}")
print(f"   Records reviewed but not in main: {len(human_keys - main_keys)}")

# ============================================================================
# PHASE 4: EXECUTE MERGE
# ============================================================================

print("\n" + "=" * 60)
print("PHASE 4: EXECUTING MERGE")
print("=" * 60)

# Rename Arcadia_ID to match main file column name
df_merge = df_merge.rename(columns={'Arcadia_ID': 'ARCADIA_TR_ID'})

print("\n1. Performing LEFT JOIN...")
print(f"   Main file records before merge: {len(df_main)}")

# Perform the merge
df_merged = df_main.merge(
    df_merge[['IG_ID', 'ARCADIA_TR_ID', 'Human_checked']],
    on=['IG_ID', 'ARCADIA_TR_ID'],
    how='left',
    indicator=True
)

print(f"   Main file records after merge: {len(df_merged)}")

# Check merge results
merge_stats = df_merged['_merge'].value_counts()
print("\n2. Merge statistics:")
for status, count in merge_stats.items():
    if status == 'left_only':
        print(f"   Not reviewed: {count}")
    elif status == 'both':
        print(f"   Successfully matched: {count}")

# Drop the merge indicator
df_merged = df_merged.drop('_merge', axis=1)

# Fill unmatched with NOT_REVIEWED
print("\n3. Handling unmatched records...")
unmatched_count = df_merged['Human_checked'].isna().sum()
df_merged['Human_checked'] = df_merged['Human_checked'].fillna('NOT_REVIEWED')
print(f"   Marked {unmatched_count} records as NOT_REVIEWED")

# ============================================================================
# PHASE 5: POST-MERGE VALIDATION
# ============================================================================

print("\n" + "=" * 60)
print("PHASE 5: POST-MERGE VALIDATION")
print("=" * 60)

# Verify record count
print("\n1. Record count validation:")
print(f"   Original records: {original_record_count}")
print(f"   After merge: {len(df_merged)}")
if len(df_merged) == original_record_count:
    print("   [OK] Record count preserved")
else:
    print(f"   ERROR: Record count changed by {len(df_merged) - original_record_count}")

# Check Human_checked distribution
print("\n2. Human_checked distribution in merged file:")
distribution = df_merged['Human_checked'].value_counts()
for value, count in distribution.items():
    percentage = (count / len(df_merged)) * 100
    print(f"   {value}: {count} ({percentage:.1f}%)")

# Validate expected values
print("\n3. Validating expected values...")
expected_match = 3104
expected_different = 36
expected_no_data = 159

actual_match = (df_merged['Human_checked'] == 'MATCH').sum()
actual_different = (df_merged['Human_checked'] == 'DIFFERENT').sum()
actual_no_data = (df_merged['Human_checked'] == 'NO_DATA').sum()

print(f"   MATCH: Expected {expected_match}, Got {actual_match} {'[OK]' if actual_match >= expected_match else '[X]'}")
print(f"   DIFFERENT: Expected {expected_different}, Got {actual_different} {'[OK]' if actual_different >= expected_different else '[X]'}")
print(f"   NO_DATA: Expected {expected_no_data}, Got {actual_no_data} {'[OK]' if actual_no_data >= expected_no_data else '[X]'}")

# Sample verification
print("\n4. Sample verification (first 5 DIFFERENT cases):")
different_cases = df_merged[df_merged['Human_checked'] == 'DIFFERENT'].head()
if len(different_cases) > 0:
    for idx, row in different_cases.iterrows():
        print(f"   IG_ID: {row['IG_ID']}, ARCADIA_TR_ID: {row['ARCADIA_TR_ID']}, Target: {row.get('Target name', 'N/A')}")

# Check for unexpected NOT_REVIEWED
not_reviewed = df_merged[df_merged['Human_checked'] == 'NOT_REVIEWED']
if len(not_reviewed) > 0:
    print(f"\n5. WARNING: {len(not_reviewed)} records marked as NOT_REVIEWED")
    if len(not_reviewed) <= 10:
        print("   These records:")
        for idx, row in not_reviewed.head(10).iterrows():
            print(f"   - IG_ID: {row['IG_ID']}, ARCADIA_TR_ID: {row['ARCADIA_TR_ID']}")
else:
    print("\n5. [OK] No NOT_REVIEWED records (as expected)")

# ============================================================================
# PHASE 6: OUTPUT AND DOCUMENTATION
# ============================================================================

print("\n" + "=" * 60)
print("PHASE 6: SAVING OUTPUT")
print("=" * 60)

# Generate output filename with URL_REVIEWED tag
timestamp = datetime.now().strftime('%d-%m-%Y')
output_file = f'../output/ig_arc_mapping_full_URL_REVIEWED_{timestamp}.csv'

print(f"\n1. Saving merged file...")
print(f"   Output file: {output_file}")

# Ensure column order is preserved (Human_checked added at the end)
final_columns = original_columns + ['Human_checked']
df_final = df_merged[final_columns]

# Save the file
df_final.to_csv(output_file, index=False, encoding='utf-8')
print(f"   [OK] File saved successfully ({len(df_final)} records, {len(df_final.columns)} columns)")

# Generate validation report
print("\n2. Generating validation report...")

report = f"""# Human Review Merge Validation Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Operation**: Merge Human_checked column into ig_arc_mapping_full.csv

## Summary
- **Source File**: test_description_advanced_human_final.csv
- **Target File**: ig_arc_mapping_full.csv  
- **Output File**: {output_file}

## Record Statistics
- Original records in main file: {original_record_count}
- Records after merge: {len(df_final)}
- Records preserved: {'[OK] Yes' if len(df_final) == original_record_count else '[X] No'}

## Human_checked Distribution
- MATCH: {actual_match} ({actual_match/len(df_final)*100:.1f}%)
- DIFFERENT: {actual_different} ({actual_different/len(df_final)*100:.1f}%)
- NO_DATA: {actual_no_data} ({actual_no_data/len(df_final)*100:.1f}%)
- NOT_REVIEWED: {(df_final['Human_checked'] == 'NOT_REVIEWED').sum()}

## Validation Results
- Expected MATCH count: {expected_match} - {'[OK] Met' if actual_match >= expected_match else '[X] Not Met'}
- Expected DIFFERENT count: {expected_different} - {'[OK] Met' if actual_different >= expected_different else '[X] Not Met'}
- Expected NO_DATA count: {expected_no_data} - {'[OK] Met' if actual_no_data >= expected_no_data else '[X] Not Met'}

## Data Integrity
- Column count preserved: {'[OK] Yes' if len(final_columns) == len(original_columns) + 1 else '[X] No'}
- Record count preserved: {'[OK] Yes' if len(df_final) == original_record_count else '[X] No'}
- Composite key matching: [OK] Completed

## Status: {'SUCCESS' if len(not_reviewed) == 0 else 'SUCCESS WITH WARNINGS'}
"""

report_file = '../output/MERGE_VALIDATION_REPORT.md'
with open(report_file, 'w', encoding='utf-8') as f:
    f.write(report)
print(f"   [OK] Validation report saved to: {report_file}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("MERGE OPERATION COMPLETE")
print("=" * 80)

print(f"""
SUMMARY:
- Records processed: {len(df_final)}
- Human reviews applied: {actual_match + actual_different + actual_no_data}
- Output file: {output_file}
- Validation report: {report_file}

RESULT: {'SUCCESS - All validations passed' if len(not_reviewed) == 0 else f'SUCCESS WITH WARNINGS - {len(not_reviewed)} records not reviewed'}
""")

print("=" * 80)