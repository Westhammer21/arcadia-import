#!/usr/bin/env python3
"""
Check for Multiple Slashes in Investor Names
=============================================
Analyze cases with more than one "/" character

Author: AI Analytics Team
Date: 2025-01-09
"""

import pandas as pd
from pathlib import Path

def analyze_multiple_slashes():
    """Check for cases with multiple slashes"""
    
    print("\n" + "="*80)
    print("ANALYZING MULTIPLE SLASH CASES")
    print("="*80)
    
    # Load original data
    base_path = Path(__file__).parent.parent
    input_path = base_path / 'output' / 'ig_arc_unmapped_vF.csv'
    
    df = pd.read_csv(input_path, encoding='utf-8')
    print(f"[INFO] Loaded {len(df)} transactions")
    
    # Get investors column
    investors = df['Investors / Buyers'].fillna('')
    
    # Count slashes in each entry
    slash_counts = investors.str.count('/')
    
    # Find cases with multiple slashes
    multiple_slashes = slash_counts > 1
    
    print(f"\n[STATISTICS]")
    print(f"Total transactions: {len(df)}")
    print(f"Transactions with 0 slashes: {(slash_counts == 0).sum()}")
    print(f"Transactions with 1 slash: {(slash_counts == 1).sum()}")
    print(f"Transactions with 2+ slashes: {(slash_counts > 1).sum()}")
    
    # Show distribution
    print(f"\n[DETAILED DISTRIBUTION]")
    for i in range(0, slash_counts.max() + 1):
        count = (slash_counts == i).sum()
        if count > 0:
            print(f"  {i} slashes: {count} transactions")
    
    # Show examples with multiple slashes
    if multiple_slashes.any():
        print(f"\n[EXAMPLES WITH MULTIPLE SLASHES]")
        multiple_slash_df = df[multiple_slashes][['Target name', 'Investors / Buyers']].copy()
        multiple_slash_df['slash_count'] = slash_counts[multiple_slashes].values
        
        # Sort by number of slashes descending
        multiple_slash_df = multiple_slash_df.sort_values('slash_count', ascending=False)
        
        for idx, row in multiple_slash_df.head(20).iterrows():
            print(f"\n[{row['slash_count']} slashes] Target: {row['Target name']}")
            print(f"  Investors: {row['Investors / Buyers']}")
            
            # Analyze the pattern
            investor_str = row['Investors / Buyers']
            
            # Check if it has (lead) marker
            has_lead = '(lead)' in investor_str.lower()
            
            # Split by slash to see the pattern
            parts = investor_str.split('/')
            print(f"  Split result ({len(parts)} parts):")
            for i, part in enumerate(parts, 1):
                print(f"    Part {i}: {part.strip()}")
            
            print(f"  Has (lead) marker: {has_lead}")
            
            # Suggest parsing approach
            if has_lead:
                print(f"  -> Will use (lead) marker for parsing (ignoring slashes)")
            else:
                print(f"  -> Multiple slashes without (lead) - needs special handling!")
    
    # Check how our current script handles these
    print(f"\n[CURRENT SCRIPT BEHAVIOR]")
    print(f"Our script uses:")
    print(f"  1. If '(lead)' exists -> split by LAST (lead) occurrence")
    print(f"  2. If '/' exists -> split by FIRST / occurrence")
    print(f"  3. Multiple slashes without (lead) -> only first / is used")
    
    # Identify potentially problematic cases
    problematic = multiple_slashes & ~investors.str.contains(r'\(lead\)', case=False, na=False)
    
    if problematic.any():
        print(f"\n[WARNING] Found {problematic.sum()} cases with multiple slashes and NO (lead) marker!")
        print(f"These might need special handling:")
        
        for idx, row in df[problematic][['Target name', 'Investors / Buyers']].head(10).iterrows():
            print(f"\n  Target: {row['Target name']}")
            print(f"  Investors: {row['Investors / Buyers']}")
    
    return df[multiple_slashes]

if __name__ == "__main__":
    multiple_slash_cases = analyze_multiple_slashes()
    print(f"\n[COMPLETE] Analysis finished")