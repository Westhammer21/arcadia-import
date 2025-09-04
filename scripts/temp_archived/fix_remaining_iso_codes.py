#!/usr/bin/env python3
"""Fix the remaining 2-letter ISO codes that were missed"""

import pandas as pd

# Additional ISO codes to fix
ADDITIONAL_ISO_CODES = {
    'JP': 'Japan',
    'BR': 'Brazil',
    'PH': 'Philippines',
    'CZ': 'Czech Republic',
    'SG': 'Singapore',
    'NL': 'Netherlands',
    'AU': 'Australia',
    'AE': 'United Arab Emirates'
}

def fix_remaining_iso_codes():
    print("Reading data...")
    df = pd.read_csv('output/ig_arc_unmapped_FINAL_COMPLETE.csv', dtype=str, na_filter=False)
    
    changes_made = 0
    
    # Process TO BE CREATED records with 2-letter codes
    to_be_created_mask = df['arc_id'] == 'TO BE CREATED'
    
    for idx in df[to_be_created_mask].index:
        current_country = df.at[idx, 'arc_hq_country']
        
        if current_country in ADDITIONAL_ISO_CODES:
            new_country = ADDITIONAL_ISO_CODES[current_country]
            df.at[idx, 'arc_hq_country'] = new_country
            target_name = df.at[idx, 'Target name']
            print(f"Row {idx+2}: {target_name}")
            print(f"  Changed: '{current_country}' -> '{new_country}'")
            changes_made += 1
    
    if changes_made > 0:
        print(f"\nSaving changes...")
        df.to_csv('output/ig_arc_unmapped_FINAL_COMPLETE.csv', index=False)
        print(f"✓ Fixed {changes_made} additional ISO codes")
    else:
        print("No additional ISO codes found to fix")
    
    return changes_made

if __name__ == "__main__":
    fix_remaining_iso_codes()