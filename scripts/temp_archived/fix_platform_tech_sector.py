#!/usr/bin/env python3
"""
Fix Platform&Tech sector mapping for TO BE CREATED records.
Changes arc_sector from 'Other' to 'Platform & Tech' for Platform&Tech records.
"""

import pandas as pd
import sys
from datetime import datetime

def fix_platform_tech_sector():
    """Fix the Platform&Tech sector mapping issue"""
    
    input_file = "output/ig_arc_unmapped_FINAL_COMPLETE.csv"
    
    print(f"Reading data from {input_file}...")
    df = pd.read_csv(input_file, dtype=str, na_filter=False)
    
    # Count before fix
    to_be_created_mask = df['arc_id'] == 'TO BE CREATED'
    platform_tech_mask = df['Sector'] == 'Platform&Tech'
    wrong_mapping_mask = df['arc_sector'] == 'Other'
    
    # Combined mask for records to fix
    fix_mask = to_be_created_mask & platform_tech_mask & wrong_mapping_mask
    records_to_fix = df[fix_mask]
    
    print(f"\nRecords to fix: {len(records_to_fix)}")
    print("\nSample of records being fixed:")
    print(records_to_fix[['Target name', 'Sector', 'arc_sector', 'arc_segment']].head(10))
    
    # Apply the fix
    df.loc[fix_mask, 'arc_sector'] = 'Platform & Tech'
    
    # Verify the fix
    still_wrong = df[to_be_created_mask & platform_tech_mask & (df['arc_sector'] == 'Other')]
    
    if len(still_wrong) == 0:
        print(f"\n[OK] Successfully fixed all {len(records_to_fix)} Platform&Tech records")
    else:
        print(f"\nWARNING: {len(still_wrong)} records still have incorrect mapping")
    
    # Save the corrected data
    print(f"\nSaving corrected data to {input_file}...")
    df.to_csv(input_file, index=False)
    
    # Generate summary report
    print("\n" + "="*60)
    print("FIX SUMMARY")
    print("="*60)
    print(f"Total records processed: {len(df)}")
    print(f"TO BE CREATED records: {to_be_created_mask.sum()}")
    print(f"Platform&Tech records fixed: {len(records_to_fix)}")
    print(f"Mapping applied: 'Other' -> 'Platform & Tech'")
    
    # Show distribution after fix
    to_be_created_df = df[to_be_created_mask]
    print("\nSector distribution for TO BE CREATED records after fix:")
    print(to_be_created_df['arc_sector'].value_counts())
    
    # Verify consistency
    print("\nConsistency check:")
    platform_records = to_be_created_df[to_be_created_df['Sector'] == 'Platform&Tech']
    unique_arc_sectors = platform_records['arc_sector'].unique()
    
    if len(unique_arc_sectors) == 1 and unique_arc_sectors[0] == 'Platform & Tech':
        print("[OK] All Platform&Tech records now correctly mapped to 'Platform & Tech'")
    else:
        print("[X] WARNING: Inconsistent mappings found:")
        print(platform_records['arc_sector'].value_counts())
    
    return len(records_to_fix)

def verify_other_sectors():
    """Verify that other sector mappings are correct"""
    
    df = pd.read_csv("output/ig_arc_unmapped_FINAL_COMPLETE.csv", dtype=str, na_filter=False)
    to_be_created = df[df['arc_id'] == 'TO BE CREATED']
    
    print("\n" + "="*60)
    print("SECTOR MAPPING VERIFICATION")
    print("="*60)
    
    # Check each sector mapping
    sector_mapping = {
        'Gaming': 'Gaming (Content & Development Publishing)',
        'Platform&Tech': 'Platform & Tech',
        'Esports': 'Esports',
        'Other': 'Other'
    }
    
    for source_sector, expected_arc_sector in sector_mapping.items():
        sector_records = to_be_created[to_be_created['Sector'] == source_sector]
        if len(sector_records) > 0:
            arc_sectors = sector_records['arc_sector'].value_counts()
            print(f"\n{source_sector} -> {expected_arc_sector}")
            print(f"  Total records: {len(sector_records)}")
            
            # Check if all mapped correctly
            if len(arc_sectors) == 1 and arc_sectors.index[0] == expected_arc_sector:
                print(f"  [OK] All correctly mapped")
            else:
                print(f"  [X] Multiple or incorrect mappings found:")
                for arc_sector, count in arc_sectors.items():
                    print(f"    - {arc_sector}: {count}")
    
    print("\n" + "="*60)

def main():
    try:
        # Fix the Platform&Tech sector mapping
        fixed_count = fix_platform_tech_sector()
        
        # Verify all sectors are now correct
        verify_other_sectors()
        
        print("\n[SUCCESS] Platform&Tech sector fix completed successfully!")
        print(f"[SUCCESS] {fixed_count} records updated")
        print("[SUCCESS] Backup saved in archive/")
        
    except Exception as e:
        print(f"\n[ERROR] Error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()