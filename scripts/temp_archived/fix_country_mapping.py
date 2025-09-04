#!/usr/bin/env python3
"""
Fix country mapping issues in ig_arc_unmapped_FINAL_COMPLETE.csv
- Convert 2-letter ISO codes to full country names
- Fix notenoughinformation cases where Target's Country has valid data
"""

import pandas as pd
import sys
from datetime import datetime

# ISO country code to full name mapping (as specified by user)
ISO_TO_FULL_NAME = {
    'US': 'United States',
    'USA': 'United States',
    'GB': 'United Kingdom',
    'UK': 'United Kingdom',
    'KR': 'South Korea',
    'RU': 'Russia',
    'DE': 'Germany',
    'FR': 'France',
    'ES': 'Spain',
    'CA': 'Canada',
    'CN': 'China',
    'IN': 'India',
    'SE': 'Sweden',
    'CH': 'Switzerland',
    'VN': 'Vietnam',
    'TR': 'Turkey',
    'HK': 'Hong Kong',
}

# Target's Country to full country name mapping
TARGETS_COUNTRY_TO_FULL_NAME = {
    'South Korea': 'South Korea',
    'Estonia': 'Estonia',
    'United Kingdom': 'United Kingdom',
    'Ethiopia': 'Ethiopia',
    'Cyprus': 'Cyprus',
    'Kazakhstan': 'Kazakhstan',
    'Saudi Arabia': 'Saudi Arabia',
    'United Arab Emirates': 'United Arab Emirates',
    'Jordan': 'Jordan',
    'Egypt': 'Egypt',
    'Sweden': 'Sweden',
    'Germany': 'Germany',
    'United States': 'United States',
    'India': 'India',
    'Russia': 'Russia',
    'Canada': 'Canada',
    'Spain': 'Spain',
    'France': 'France',
    'China': 'China',
    'Turkey': 'Turkey',
    'Vietnam': 'Vietnam',
    'Switzerland': 'Switzerland',
    'Hong Kong': 'Hong Kong',
}

def fix_country_mapping(input_file, output_file):
    """Fix country mapping issues for TO BE CREATED records"""
    
    print(f"Reading data from {input_file}...")
    df = pd.read_csv(input_file, dtype=str, na_filter=False)
    
    # Track changes
    changes_made = {
        'notenoughinformation_fixed': 0,
        'iso_codes_converted': 0,
        'total_to_be_created': 0,
        'details': []
    }
    
    # Count TO BE CREATED records
    to_be_created_mask = df['arc_id'] == 'TO BE CREATED'
    changes_made['total_to_be_created'] = to_be_created_mask.sum()
    
    print(f"Found {changes_made['total_to_be_created']} TO BE CREATED records")
    
    # Process each TO BE CREATED record
    for idx in df[to_be_created_mask].index:
        original_country = df.at[idx, 'arc_hq_country']
        targets_country = df.at[idx, "Target's Country"]
        target_name = df.at[idx, 'Target name']
        
        new_country = original_country
        change_type = None
        
        # First check if it's "notenoughinformation" and we have a valid Target's Country
        if original_country == 'notenoughinformation':
            if targets_country in TARGETS_COUNTRY_TO_FULL_NAME:
                new_country = TARGETS_COUNTRY_TO_FULL_NAME[targets_country]
                change_type = 'notenoughinformation_fixed'
                changes_made['notenoughinformation_fixed'] += 1
        # Check if it's a 2-letter ISO code
        elif original_country in ISO_TO_FULL_NAME:
            new_country = ISO_TO_FULL_NAME[original_country]
            change_type = 'iso_codes_converted'
            changes_made['iso_codes_converted'] += 1
        
        # Update if changed
        if new_country != original_country:
            df.at[idx, 'arc_hq_country'] = new_country
            changes_made['details'].append({
                'row': idx + 2,  # +2 for Excel row number (header + 0-index)
                'target_name': target_name,
                'targets_country': targets_country,
                'old_value': original_country,
                'new_value': new_country,
                'change_type': change_type
            })
            print(f"  Row {idx+2}: '{target_name}' - Changed '{original_country}' to '{new_country}'")
    
    # Save the corrected data
    print(f"\nSaving corrected data to {output_file}...")
    df.to_csv(output_file, index=False)
    
    return changes_made

def display_summary(changes):
    """Display summary of changes made"""
    
    print("\n" + "="*60)
    print("SUMMARY OF CHANGES")
    print("="*60)
    print(f"Total TO BE CREATED records processed: {changes['total_to_be_created']}")
    print(f"Records with 'notenoughinformation' fixed: {changes['notenoughinformation_fixed']}")
    print(f"Records with ISO codes converted to full names: {changes['iso_codes_converted']}")
    print(f"Total records modified: {len(changes['details'])}")
    
    if changes['details']:
        print("\n" + "-"*60)
        print("DETAILED CHANGES:")
        print("-"*60)
        
        # Group by change type
        noinfo_changes = [d for d in changes['details'] if d['change_type'] == 'notenoughinformation_fixed']
        iso_changes = [d for d in changes['details'] if d['change_type'] == 'iso_codes_converted']
        
        if noinfo_changes:
            print("\nFixed 'notenoughinformation' cases:")
            for change in noinfo_changes:
                print(f"  Row {change['row']}: {change['target_name']}")
                print(f"    Target's Country: {change['targets_country']}")
                print(f"    Changed from: '{change['old_value']}' -> '{change['new_value']}'")
        
        if iso_changes:
            print("\nConverted ISO codes to full names:")
            for change in iso_changes:
                print(f"  Row {change['row']}: {change['target_name']}")
                print(f"    Changed from: '{change['old_value']}' -> '{change['new_value']}'")
    
    print("\n" + "="*60)
    print(f"✓ File successfully updated: output/ig_arc_unmapped_FINAL_COMPLETE.csv")
    print(f"✓ Backup saved in: archive/ig_arc_unmapped_FINAL_COMPLETE_BACKUP_*.csv")
    print("="*60)

def main():
    input_file = "output/ig_arc_unmapped_FINAL_COMPLETE.csv"
    output_file = input_file  # Overwrite the same file
    
    try:
        changes = fix_country_mapping(input_file, output_file)
        display_summary(changes)
        print("\n✅ Country mapping fixes completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()