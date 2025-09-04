"""
Carefully analyze the human-verified duplicates file
This is CRITICAL data - only real duplicates verified by human
"""
import pandas as pd
import numpy as np

print("=" * 70)
print("ANALYZING HUMAN-VERIFIED DUPLICATES (CRITICAL DATA)")
print("=" * 70)

# Read the tab-delimited file with proper encoding
print("\n1. READING FILE...")
try:
    # Try different encodings
    for encoding in ['utf-8', 'windows-1251', 'cp1252', 'latin1']:
        try:
            df_verified = pd.read_csv(
                'output/Correct Transaction Imported.csv',
                sep='\t',  # Tab-delimited
                encoding=encoding
            )
            print(f"   Successfully read with {encoding} encoding")
            print(f"   Rows: {len(df_verified)}, Columns: {len(df_verified.columns)}")
            break
        except:
            continue
except Exception as e:
    print(f"   ERROR: {e}")
    exit(1)

# Display columns
print("\n2. COLUMN STRUCTURE:")
print("   Columns in verified duplicates file:")
for i, col in enumerate(df_verified.columns, 1):
    print(f"   {i:2}. {col}")

# Focus on ID-related columns
print("\n3. ID COLUMNS ANALYSIS:")
id_columns = ['ig_id', 'arc_id', 'A_TR_ID']
for col in id_columns:
    if col in df_verified.columns:
        non_null = df_verified[col].notna().sum()
        unique = df_verified[col].nunique()
        print(f"\n   {col}:")
        print(f"   - Non-null values: {non_null}/{len(df_verified)}")
        print(f"   - Unique values: {unique}")
        print(f"   - Sample values: {df_verified[col].head(3).tolist()}")

# Critical mapping check
print("\n4. CRITICAL MAPPING: A_TR_ID to arcadia_database_with_ids.csv")
print("   " + "=" * 60)

# Read arcadia database to verify mapping
arcadia_db = pd.read_csv('output/arcadia_database_with_ids.csv')
print(f"   Arcadia database: {len(arcadia_db)} rows")

# Check mapping integrity
print("\n   Verifying A_TR_ID mapping to Arcadia database:")
if 'A_TR_ID' in df_verified.columns:
    # Get all A_TR_IDs from verified duplicates
    verified_ids = df_verified['A_TR_ID'].dropna().unique()
    print(f"   - Total unique A_TR_IDs in verified duplicates: {len(verified_ids)}")
    
    # Check if these IDs exist in arcadia database
    arcadia_ids = arcadia_db['ID'].unique()
    matching_ids = set(verified_ids) & set(arcadia_ids)
    missing_ids = set(verified_ids) - set(arcadia_ids)
    
    print(f"   - IDs found in Arcadia database: {len(matching_ids)}")
    print(f"   - IDs NOT found in Arcadia database: {len(missing_ids)}")
    
    if missing_ids and len(missing_ids) < 10:
        print(f"     Missing IDs: {list(missing_ids)[:10]}")

# Analyze the verified duplicates
print("\n5. VERIFIED DUPLICATES ANALYSIS:")
print("   " + "=" * 60)

# Check DUPLICATE? column
if 'DUPLICATE?' in df_verified.columns:
    dup_counts = df_verified['DUPLICATE?'].value_counts()
    print("\n   DUPLICATE? column distribution:")
    for val, count in dup_counts.items():
        print(f"   - {val}: {count}")

# Check confidence levels
if 'confidence' in df_verified.columns:
    conf_counts = df_verified['confidence'].value_counts().sort_index(ascending=False)
    print("\n   Confidence level distribution:")
    for conf, count in conf_counts.items():
        print(f"   - {conf}%: {count}")

# Check Manual Check column
manual_col = 'Manual Check (DUPLICATE?)'
if manual_col in df_verified.columns:
    manual_counts = df_verified[manual_col].value_counts()
    print(f"\n   {manual_col} distribution:")
    for val, count in manual_counts.items():
        print(f"   - {val}: {count}")
    empty_manual = df_verified[manual_col].isna().sum()
    print(f"   - Empty/NaN: {empty_manual}")

# Sample data
print("\n6. SAMPLE DATA (first 5 rows):")
print("   " + "=" * 60)
display_cols = ['ig_id', 'arc_id', 'A_TR_ID', 'ig_target', 'arc_target', 'DUPLICATE?']
if all(col in df_verified.columns for col in display_cols):
    print(df_verified[display_cols].head().to_string())

# Understand the relationship between arc_id and A_TR_ID
print("\n7. UNDERSTANDING arc_id vs A_TR_ID RELATIONSHIP:")
print("   " + "=" * 60)
if 'arc_id' in df_verified.columns and 'A_TR_ID' in df_verified.columns:
    # Sample mapping
    sample = df_verified[['arc_id', 'A_TR_ID', 'arc_target']].head(10)
    print("\n   Sample mappings:")
    for _, row in sample.iterrows():
        arc_id = row['arc_id']
        a_tr_id = row['A_TR_ID']
        target = row['arc_target']
        
        # Verify in arcadia database
        if arc_id < len(arcadia_db):
            actual_id = arcadia_db.loc[arc_id, 'ID']
            actual_company = arcadia_db.loc[arc_id, 'Target Company']
            match = "OK" if actual_id == a_tr_id else "ERROR"
            print(f"   arc_id={arc_id} -> A_TR_ID={a_tr_id} (actual ID={actual_id}) {match} [{target}]")

# Save analysis summary
print("\n8. SAVING ANALYSIS SUMMARY:")
summary = {
    'total_verified_duplicates': len(df_verified),
    'unique_ig_transactions': df_verified['ig_id'].nunique() if 'ig_id' in df_verified.columns else 0,
    'unique_arc_transactions': df_verified['A_TR_ID'].nunique() if 'A_TR_ID' in df_verified.columns else 0,
    'confidence_100_pct': len(df_verified[df_verified['confidence'] == 100]) if 'confidence' in df_verified.columns else 0,
    'all_marked_yes': all(df_verified['DUPLICATE?'] == 'YES') if 'DUPLICATE?' in df_verified.columns else False
}

print("\n   Summary:")
for key, value in summary.items():
    print(f"   - {key}: {value}")

# Create a list of Arcadia IDs to exclude from future analysis
if 'A_TR_ID' in df_verified.columns:
    exclude_ids = df_verified['A_TR_ID'].dropna().unique().tolist()
    
    # Save to file
    import json
    with open('output/verified_duplicate_arcadia_ids.json', 'w') as f:
        json.dump(exclude_ids, f, indent=2)
    
    print(f"\n   Saved {len(exclude_ids)} Arcadia IDs to exclude from future analysis")
    print("   File: output/verified_duplicate_arcadia_ids.json")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE - DATA READY FOR EXCLUSION FROM FUTURE ANALYSIS")
print("=" * 70)