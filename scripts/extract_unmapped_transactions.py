#!/usr/bin/env python3
"""
Extract Unmapped InvestGame Transactions
=========================================
Creates a subset of ig_arc_mapping_full_vF.csv containing only transactions
that are NOT mapped to Arcadia (where ARCADIA_TR_ID is empty/null).

Author: AI Analytics Team
Date: 2025-09-03
"""

import pandas as pd
import numpy as np
from pathlib import Path

def main():
    """Extract unmapped transactions from master mapping file."""
    
    print("\n" + "="*80)
    print(" EXTRACTING UNMAPPED INVESTGAME TRANSACTIONS")
    print("="*80)
    
    # Define paths
    base_path = Path(__file__).parent.parent
    input_file = base_path / 'output' / 'ig_arc_mapping_full_vF.csv'
    output_file = base_path / 'output' / 'ig_arc_unmapped.csv'
    
    # Step 1: Read master file
    print("\n[Step 1] Reading master mapping file...")
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"  Total records loaded: {len(df)}")
    print(f"  Total columns: {len(df.columns)}")
    
    # Step 2: Identify unmapped transactions
    print("\n[Step 2] Identifying unmapped transactions...")
    
    # Check for unmapped (ARCADIA_TR_ID is NaN or empty string)
    unmapped_mask = df['ARCADIA_TR_ID'].isna() | (df['ARCADIA_TR_ID'] == '')
    df_unmapped = df[unmapped_mask].copy()
    
    print(f"  Unmapped transactions found: {len(df_unmapped)}")
    print(f"  Mapped transactions: {len(df) - len(df_unmapped)}")
    print(f"  Percentage unmapped: {len(df_unmapped)/len(df)*100:.1f}%")
    
    # Step 3: Select only InvestGame columns (exclude ARC_* and mapping columns)
    print("\n[Step 3] Selecting InvestGame columns only...")
    
    # Define columns to keep (original InvestGame columns + IG_ID)
    ig_columns = [
        'Date', 'Year', 'Quarter', 'Target name', 'Investors / Buyers',
        'Type', 'Category', 'AI', 'Size, $m', '% acquired',
        'Sector', 'Segment', "Target's Country", 'Region', 'Target Founded',
        'Gender', "Target's Website", 'Short Deal Description', 'Deal Link',
        'Amount_Status', 'IG_ID'
    ]
    
    # Verify all columns exist
    missing_cols = [col for col in ig_columns if col not in df_unmapped.columns]
    if missing_cols:
        print(f"  WARNING: Missing columns: {missing_cols}")
    
    # Select only IG columns
    df_unmapped_clean = df_unmapped[ig_columns].copy()
    print(f"  Columns selected: {len(df_unmapped_clean.columns)}")
    
    # Step 4: Validation
    print("\n[Step 4] Validating data integrity...")
    
    # Check for any ARC_ columns (should be none)
    arc_cols = [col for col in df_unmapped_clean.columns if col.startswith('ARC_')]
    if arc_cols:
        print(f"  ERROR: Found ARC_ columns that shouldn't be here: {arc_cols}")
    else:
        print(f"  [OK] No ARC_ columns present")
    
    # Check for ARCADIA_TR_ID column (should not be present)
    if 'ARCADIA_TR_ID' in df_unmapped_clean.columns:
        print(f"  ERROR: ARCADIA_TR_ID column still present")
    else:
        print(f"  [OK] ARCADIA_TR_ID column excluded")
    
    # Sample validation - show first few records
    print("\n[Sample Records]")
    print("First 3 unmapped transactions:")
    for idx in range(min(3, len(df_unmapped_clean))):
        row = df_unmapped_clean.iloc[idx]
        print(f"  {idx+1}. IG_ID: {row['IG_ID']}, Target: {row['Target name']}, "
              f"Date: {row['Date']}, Type: {row['Type']}")
    
    # Step 5: Save the file
    print(f"\n[Step 5] Saving unmapped transactions to output/ig_arc_unmapped.csv...")
    df_unmapped_clean.to_csv(output_file, index=False, encoding='utf-8')
    print(f"  [OK] File saved successfully")
    
    # Step 6: Summary statistics
    print("\n" + "="*80)
    print(" SUMMARY STATISTICS")
    print("="*80)
    
    # By year
    year_counts = df_unmapped_clean['Year'].value_counts().sort_index()
    print("\nUnmapped by Year:")
    for year, count in year_counts.items():
        print(f"  {year}: {count} transactions")
    
    # By category
    category_counts = df_unmapped_clean['Category'].value_counts().head(5)
    print("\nTop 5 Categories (Unmapped):")
    for cat, count in category_counts.items():
        print(f"  {cat}: {count} transactions")
    
    # By type
    type_counts = df_unmapped_clean['Type'].value_counts().head(5)
    print("\nTop 5 Types (Unmapped):")
    for typ, count in type_counts.items():
        print(f"  {typ}: {count} transactions")
    
    print("\n" + "="*80)
    print(" EXTRACTION COMPLETE")
    print("="*80)
    print(f"\nFinal Statistics:")
    print(f"  Original records: {len(df)}")
    print(f"  Unmapped extracted: {len(df_unmapped_clean)}")
    print(f"  Columns in output: {len(df_unmapped_clean.columns)}")
    print(f"  Output file: {output_file}")
    print(f"\n[SUCCESS] Created ig_arc_unmapped.csv with {len(df_unmapped_clean)} unmapped transactions")
    
    return df_unmapped_clean

if __name__ == "__main__":
    df_result = main()