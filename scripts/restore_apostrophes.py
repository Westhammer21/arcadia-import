#!/usr/bin/env python3
"""
Restore apostrophes that were incorrectly removed
Created: 2025-09-03
Purpose: Fix specific names that should have apostrophes
"""

import pandas as pd
from datetime import datetime
from pathlib import Path

def main():
    """Main execution function"""
    
    print("=" * 70)
    print("RESTORING APOSTROPHES IN COMPANY NAMES")
    print("=" * 70)
    
    # File paths
    input_file = Path('../output/ig_arc_unmapped_FINAL_COMPLETE.csv')
    output_file = Path('../output/ig_arc_unmapped_FINAL_COMPLETE.csv')
    
    # Load data
    print("\n1. Loading data")
    print("-" * 50)
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"   Loaded {len(df)} records")
    
    # Define corrections needed (based on what should have apostrophes)
    apostrophe_fixes = {
        'Were Five Games': "We're Five Games",
        'Thats No Moon Entertainment': "That's No Moon Entertainment",
        'Bhooshans Junior': "Bhooshan's Junior",
        'Dont Nod Entertainment': "Don't Nod Entertainment",
        'Gullivers Games': "Gulliver's Games",
        'N3tworks platform': "N3twork's platform"
    }
    
    print("\n2. Applying apostrophe corrections")
    print("-" * 50)
    
    changes_made = 0
    
    for col in ['Target name', 'Investors / Buyers', 'Short description']:
        if col in df.columns:
            for wrong, correct in apostrophe_fixes.items():
                # Check if this exact wrong version exists
                mask = df[col] == wrong
                if mask.any():
                    df.loc[mask, col] = correct
                    count = mask.sum()
                    changes_made += count
                    print(f"   Fixed '{wrong}' -> '{correct}' ({count} occurrences in {col})")
                
                # Also check for partial matches in longer strings
                partial_mask = df[col].astype(str).str.contains(wrong, case=False, na=False, regex=False)
                if partial_mask.any():
                    for idx in df[partial_mask].index:
                        original = df.at[idx, col]
                        fixed = original.replace(wrong, correct)
                        if fixed != original:
                            df.at[idx, col] = fixed
                            changes_made += 1
                            print(f"   Fixed partial match in {col} row {idx+2}")
    
    # Also check in arc_name column if it exists
    if 'arc_name' in df.columns:
        for wrong, correct in apostrophe_fixes.items():
            mask = df['arc_name'] == wrong
            if mask.any():
                df.loc[mask, 'arc_name'] = correct
                count = mask.sum()
                changes_made += count
                print(f"   Fixed '{wrong}' -> '{correct}' ({count} occurrences in arc_name)")
    
    # Save corrected file
    print("\n3. Saving corrected file")
    print("-" * 50)
    print(f"   Output: {output_file}")
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"   Total corrections: {changes_made}")
    
    # Verify the fixes
    print("\n4. Verifying apostrophe restorations")
    print("-" * 50)
    
    for correct in apostrophe_fixes.values():
        # Extract the first word for searching
        first_word = correct.split()[0].replace("'", "")
        
        # Search in Target name
        mask = df['Target name'].astype(str).str.contains(first_word, case=False, na=False)
        if mask.any():
            sample = df[mask].iloc[0]['Target name']
            if "'" in sample:
                print(f"   OK: '{sample}'")
            else:
                print(f"   CHECK: '{sample}' (might need apostrophe)")
    
    print("\n" + "=" * 70)
    print("APOSTROPHE RESTORATION COMPLETE!")
    print("=" * 70)

if __name__ == "__main__":
    main()