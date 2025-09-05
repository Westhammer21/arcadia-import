#!/usr/bin/env python3
"""
Comprehensive Arcadia-InvestGame Mapping Verification
======================================================
Verifies:
1. All Arcadia transactions are properly mapped
2. No duplicate Arcadia ID assignments
3. Unmapped transactions are only pre-2020 or DISABLED

Author: AI Analytics Team
Date: 2025-09-03
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

def load_data():
    """Load both databases."""
    print("\n" + "="*80)
    print("LOADING DATA FILES")
    print("="*80)
    
    base_path = Path(__file__).parent.parent
    
    # Load Arcadia database
    arcadia_path = base_path / 'src' / 'arcadia_database_2025-09-03.csv'
    df_arcadia = pd.read_csv(arcadia_path, encoding='utf-8')
    print(f"[OK] Loaded Arcadia database: {len(df_arcadia)} transactions")
    
    # Load updated IG mapping
    ig_path = base_path / 'output' / 'ig_arc_mapping_full_UPDATED_20250903_123917.csv'
    df_ig = pd.read_csv(ig_path, encoding='utf-8')
    print(f"[OK] Loaded IG mapping: {len(df_ig)} transactions")
    
    return df_arcadia, df_ig

def extract_mapped_ids(df_ig):
    """Extract all ARCADIA_TR_IDs from IG mapping."""
    print("\n" + "="*80)
    print("EXTRACTING MAPPED IDS")
    print("="*80)
    
    # Get non-null ARCADIA_TR_IDs
    mapped_ids = df_ig['ARCADIA_TR_ID'].dropna()
    
    # Convert to integers (handle floats)
    mapped_ids_clean = []
    for val in mapped_ids:
        try:
            mapped_ids_clean.append(int(float(val)))
        except:
            pass
    
    mapped_ids_set = set(mapped_ids_clean)
    print(f"[OK] Found {len(mapped_ids_set)} unique Arcadia IDs in IG mapping")
    
    return mapped_ids_set, mapped_ids_clean

def check_duplicate_assignments(mapped_ids_list):
    """Check for duplicate Arcadia ID assignments."""
    print("\n" + "="*80)
    print("CHECKING FOR DUPLICATE ARCADIA ID ASSIGNMENTS")
    print("="*80)
    
    from collections import Counter
    
    # Count occurrences
    id_counts = Counter(mapped_ids_list)
    
    # Find duplicates
    duplicates = {id_: count for id_, count in id_counts.items() if count > 1}
    
    if duplicates:
        print(f"[WARNING] Found {len(duplicates)} Arcadia IDs assigned to multiple IG deals:")
        for arc_id, count in sorted(duplicates.items())[:10]:  # Show first 10
            print(f"  - Arcadia ID {arc_id}: assigned to {count} IG deals")
    else:
        print("[OK] No duplicate Arcadia ID assignments found")
    
    return duplicates

def find_unmapped_arcadia(df_arcadia, mapped_ids_set):
    """Find Arcadia transactions not mapped to InvestGame."""
    print("\n" + "="*80)
    print("FINDING UNMAPPED ARCADIA TRANSACTIONS")
    print("="*80)
    
    # Convert Arcadia IDs to int
    df_arcadia['ID_int'] = df_arcadia['ID'].astype(int)
    
    # Find unmapped
    unmapped_mask = ~df_arcadia['ID_int'].isin(mapped_ids_set)
    df_unmapped = df_arcadia[unmapped_mask].copy()
    
    print(f"[INFO] Total Arcadia transactions: {len(df_arcadia)}")
    print(f"[INFO] Mapped to InvestGame: {len(df_arcadia) - len(df_unmapped)}")
    print(f"[INFO] Unmapped transactions: {len(df_unmapped)}")
    
    return df_unmapped

def parse_date(date_str):
    """Parse date in YYYY-MM-DD or DD/MM/YYYY format."""
    if pd.isna(date_str) or date_str == '':
        return None
    
    # Try YYYY-MM-DD format first
    try:
        return datetime.strptime(str(date_str), '%Y-%m-%d')
    except:
        pass
    
    # Try DD/MM/YYYY format
    try:
        return datetime.strptime(str(date_str), '%d/%m/%Y')
    except:
        pass
    
    # Try YYYY-DD-MM (in case of confusion)
    try:
        return datetime.strptime(str(date_str), '%Y-%d-%m')
    except:
        pass
        
    return None

def verify_unmapped_criteria(df_unmapped):
    """Verify unmapped transactions meet criteria (pre-2020 or DISABLED)."""
    print("\n" + "="*80)
    print("VERIFYING UNMAPPED CRITERIA")
    print("="*80)
    
    cutoff_date = datetime(2020, 1, 1)
    
    # Initialize categories
    pre_2020 = []
    disabled = []
    unexpected = []
    
    for idx, row in df_unmapped.iterrows():
        is_pre_2020 = False
        is_disabled = False
        
        # Check status
        if 'Status*' in row and str(row['Status*']).upper() == 'DISABLED':
            is_disabled = True
            disabled.append(row)
        
        # Check dates
        announcement_date = parse_date(row.get('Announcement date*', ''))
        closed_date = parse_date(row.get('closed date', ''))
        
        if announcement_date and announcement_date < cutoff_date:
            is_pre_2020 = True
            if not is_disabled:
                pre_2020.append(row)
        elif closed_date and closed_date < cutoff_date:
            is_pre_2020 = True
            if not is_disabled:
                pre_2020.append(row)
        
        # Check if neither criteria is met
        if not is_pre_2020 and not is_disabled:
            unexpected.append(row)
    
    print(f"\nUnmapped Transaction Categories:")
    print(f"  Pre-2020 dates: {len(pre_2020)}")
    print(f"  DISABLED status: {len(disabled)}")
    print(f"  UNEXPECTED (neither pre-2020 nor DISABLED): {len(unexpected)}")
    
    if unexpected:
        print(f"\n[WARNING] Found {len(unexpected)} unexpected unmapped transactions!")
        print("First 10 unexpected unmapped transactions:")
        for row in unexpected[:10]:
            print(f"  ID: {row['ID']}, Status: {row.get('Status*', 'N/A')}, "
                  f"Announcement: {row.get('Announcement date*', 'N/A')}, "
                  f"Company: {row.get('Target Company', 'N/A')}")
    
    return pre_2020, disabled, unexpected

def check_specific_duplicates(df_ig, duplicates):
    """Get details about duplicate assignments."""
    print("\n" + "="*80)
    print("DUPLICATE ASSIGNMENT DETAILS")
    print("="*80)
    
    if not duplicates:
        print("No duplicates to analyze")
        return
    
    for arc_id, count in sorted(duplicates.items())[:5]:  # Show details for first 5
        print(f"\n[Arcadia ID {arc_id}] - Assigned to {count} IG deals:")
        
        # Find all IG records with this Arcadia ID
        mask = df_ig['ARCADIA_TR_ID'].apply(
            lambda x: str(int(float(x))) == str(arc_id) if pd.notna(x) else False
        )
        
        duplicate_records = df_ig[mask][['IG_ID', 'Target name', 'Date', 'ARCADIA_TR_ID']]
        for _, rec in duplicate_records.iterrows():
            print(f"  - IG_ID: {rec['IG_ID']}, Target: {rec['Target name']}, Date: {rec['Date']}")

def create_summary_report(df_arcadia, df_ig, mapped_ids_set, duplicates, 
                         pre_2020, disabled, unexpected):
    """Create comprehensive summary report."""
    print("\n" + "="*80)
    print("SUMMARY REPORT")
    print("="*80)
    
    total_arcadia = len(df_arcadia)
    total_ig = len(df_ig)
    mapped_count = len(mapped_ids_set)
    unmapped_count = total_arcadia - mapped_count
    
    print(f"""
ARCADIA-INVESTGAME MAPPING VERIFICATION REPORT
==============================================

1. DATABASE OVERVIEW:
   - Total Arcadia transactions: {total_arcadia}
   - Total InvestGame transactions: {total_ig}
   - Unique Arcadia IDs mapped to IG: {mapped_count}

2. MAPPING COVERAGE:
   - Arcadia transactions mapped: {mapped_count} ({mapped_count/total_arcadia*100:.1f}%)
   - Arcadia transactions unmapped: {unmapped_count} ({unmapped_count/total_arcadia*100:.1f}%)

3. DUPLICATE ASSIGNMENTS:
   - Arcadia IDs used multiple times: {len(duplicates)}
   - Total duplicate assignments: {sum(duplicates.values()) - len(duplicates) if duplicates else 0}

4. UNMAPPED TRANSACTION ANALYSIS:
   - Pre-2020 transactions: {len(pre_2020)} [OK] (Expected)
   - DISABLED status: {len(disabled)} [OK] (Expected)
   - UNEXPECTED unmapped: {len(unexpected)} {'[WARNING] NEEDS REVIEW' if unexpected else '[OK]'}
   
5. DATA INTEGRITY:
   - Duplicate ID assignments: {'[WARNING] FOUND' if duplicates else '[OK] NONE'}
   - Unexpected unmapped: {'[WARNING] FOUND' if unexpected else '[OK] NONE'}
""")
    
    # Save detailed reports
    output_path = Path(__file__).parent.parent / 'output'
    
    # Save unexpected unmapped if any
    if unexpected:
        unexpected_df = pd.DataFrame(unexpected)
        unexpected_df.to_csv(output_path / 'unexpected_unmapped_arcadia.csv', index=False)
        print(f"\n[WARNING] Unexpected unmapped transactions saved to: unexpected_unmapped_arcadia.csv")
    
    # Save duplicates if any
    if duplicates:
        dup_report = pd.DataFrame([
            {'Arcadia_ID': k, 'Times_Used': v} 
            for k, v in duplicates.items()
        ]).sort_values('Times_Used', ascending=False)
        dup_report.to_csv(output_path / 'duplicate_arcadia_assignments.csv', index=False)
        print(f"[WARNING] Duplicate assignments saved to: duplicate_arcadia_assignments.csv")
    
    # Save full unmapped list
    unmapped_all = pre_2020 + disabled + unexpected
    if unmapped_all:
        unmapped_df = pd.DataFrame(unmapped_all)
        
        # Add category column
        categories = []
        for row in unmapped_all:
            if row in pre_2020:
                categories.append('PRE_2020')
            elif row in disabled:
                categories.append('DISABLED')
            else:
                categories.append('UNEXPECTED')
        
        unmapped_df['Unmapped_Reason'] = categories
        unmapped_df.to_csv(output_path / 'all_unmapped_arcadia.csv', index=False)
        print(f"\n[OK] Complete unmapped list saved to: all_unmapped_arcadia.csv")

    # Save summary JSON
    summary = {
        'verification_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'database_stats': {
            'total_arcadia': int(total_arcadia),
            'total_investgame': int(total_ig),
            'mapped_arcadia_ids': int(mapped_count),
            'unmapped_arcadia': int(unmapped_count)
        },
        'coverage': {
            'mapped_percentage': round(mapped_count/total_arcadia*100, 2),
            'unmapped_percentage': round(unmapped_count/total_arcadia*100, 2)
        },
        'duplicates': {
            'unique_ids_duplicated': len(duplicates),
            'total_duplicate_assignments': sum(duplicates.values()) - len(duplicates) if duplicates else 0
        },
        'unmapped_analysis': {
            'pre_2020': len(pre_2020),
            'disabled': len(disabled),
            'unexpected': len(unexpected)
        },
        'data_integrity': {
            'has_duplicates': len(duplicates) > 0,
            'has_unexpected_unmapped': len(unexpected) > 0
        }
    }
    
    summary_path = output_path / 'arcadia_mapping_verification_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"[OK] Summary JSON saved to: {summary_path}")

def main():
    """Main execution function."""
    print("\n" + "="*80)
    print(" COMPREHENSIVE ARCADIA-INVESTGAME MAPPING VERIFICATION")
    print("="*80)
    
    try:
        # Load data
        df_arcadia, df_ig = load_data()
        
        # Extract mapped IDs
        mapped_ids_set, mapped_ids_list = extract_mapped_ids(df_ig)
        
        # Check for duplicates
        duplicates = check_duplicate_assignments(mapped_ids_list)
        
        # Find unmapped Arcadia transactions
        df_unmapped = find_unmapped_arcadia(df_arcadia, mapped_ids_set)
        
        # Verify unmapped criteria
        pre_2020, disabled, unexpected = verify_unmapped_criteria(df_unmapped)
        
        # Show duplicate details if any
        if duplicates:
            check_specific_duplicates(df_ig, duplicates)
        
        # Create summary report
        create_summary_report(df_arcadia, df_ig, mapped_ids_set, duplicates,
                             pre_2020, disabled, unexpected)
        
        print("\n" + "="*80)
        print(" [OK] VERIFICATION COMPLETED")
        print("="*80)
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())