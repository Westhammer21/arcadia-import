#!/usr/bin/env python3
"""
Validate Unmapped Extraction
============================
Validates that ig_arc_unmapped.csv was created correctly.

Author: AI Analytics Team  
Date: 2025-09-03
"""

import pandas as pd
from pathlib import Path

def validate():
    """Validate the unmapped extraction."""
    
    print("\n" + "="*80)
    print(" VALIDATING UNMAPPED EXTRACTION")
    print("="*80)
    
    base_path = Path(__file__).parent.parent
    
    # Load both files
    master_file = base_path / 'output' / 'ig_arc_mapping_full_vF.csv'
    unmapped_file = base_path / 'output' / 'ig_arc_unmapped.csv'
    
    df_master = pd.read_csv(master_file, encoding='utf-8')
    df_unmapped = pd.read_csv(unmapped_file, encoding='utf-8')
    
    print("\n[1] File Statistics:")
    print(f"  Master file: {len(df_master)} records")
    print(f"  Unmapped file: {len(df_unmapped)} records")
    
    # Check unmapped count in master
    unmapped_in_master = df_master['ARCADIA_TR_ID'].isna() | (df_master['ARCADIA_TR_ID'] == '')
    unmapped_count = unmapped_in_master.sum()
    
    print(f"\n[2] Validation Checks:")
    print(f"  Unmapped in master: {unmapped_count}")
    print(f"  Records in unmapped file: {len(df_unmapped)}")
    
    if unmapped_count == len(df_unmapped):
        print(f"  [OK] Count matches perfectly!")
    else:
        print(f"  [ERROR] Count mismatch! Difference: {unmapped_count - len(df_unmapped)}")
    
    # Check columns
    print(f"\n[3] Column Validation:")
    print(f"  Columns in unmapped file: {len(df_unmapped.columns)}")
    
    # Check for excluded columns
    excluded_cols = ['ARCADIA_TR_ID', 'ARCADIA_TR_URL', 'Human_checked']
    arc_cols = [col for col in df_unmapped.columns if col.startswith('ARC_')]
    
    issues = []
    for col in excluded_cols:
        if col in df_unmapped.columns:
            issues.append(col)
    
    if arc_cols:
        issues.extend(arc_cols)
    
    if issues:
        print(f"  [ERROR] Found columns that should be excluded: {issues}")
    else:
        print(f"  [OK] No excluded columns found")
    
    # Verify IG_ID matches
    print(f"\n[4] IG_ID Verification:")
    
    # Get IG_IDs of unmapped from master
    unmapped_ids_master = df_master[unmapped_in_master]['IG_ID'].values
    unmapped_ids_file = df_unmapped['IG_ID'].values
    
    # Check if all IDs match
    if set(unmapped_ids_master) == set(unmapped_ids_file):
        print(f"  [OK] All IG_IDs match between files")
    else:
        missing = set(unmapped_ids_master) - set(unmapped_ids_file)
        extra = set(unmapped_ids_file) - set(unmapped_ids_master)
        if missing:
            print(f"  [ERROR] Missing IG_IDs: {list(missing)[:10]}")
        if extra:
            print(f"  [ERROR] Extra IG_IDs: {list(extra)[:10]}")
    
    # Sample comparison
    print(f"\n[5] Sample Data Verification:")
    sample_ig_id = df_unmapped.iloc[0]['IG_ID']
    
    # Get from master
    master_row = df_master[df_master['IG_ID'] == sample_ig_id].iloc[0]
    unmapped_row = df_unmapped[df_unmapped['IG_ID'] == sample_ig_id].iloc[0]
    
    print(f"  Sample IG_ID: {sample_ig_id}")
    print(f"  Master - Target: {master_row['Target name']}")
    print(f"  Unmapped - Target: {unmapped_row['Target name']}")
    
    if master_row['Target name'] == unmapped_row['Target name']:
        print(f"  [OK] Data matches")
    else:
        print(f"  [ERROR] Data mismatch!")
    
    print("\n" + "="*80)
    print(" VALIDATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    validate()