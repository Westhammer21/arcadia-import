#!/usr/bin/env python3
"""
Analyze Cases Without Clear Role Delimiters
============================================
Check how we handled cases with multiple investors but no (lead) or / markers

Author: AI Analytics Team
Date: 2025-01-09
"""

import pandas as pd
from pathlib import Path

def analyze_no_delimiter_cases():
    """Analyze cases processed without clear delimiters"""
    
    print("\n" + "="*80)
    print("ANALYZING CASES WITHOUT CLEAR DELIMITERS")
    print("="*80)
    
    # Load processed data
    base_path = Path(__file__).parent.parent
    processed_path = base_path / 'output' / 'ig_arc_unmapped_investors_complex_v2.csv'
    original_path = base_path / 'output' / 'ig_arc_unmapped_vF.csv'
    
    processed_df = pd.read_csv(processed_path, encoding='utf-8')
    original_df = pd.read_csv(original_path, encoding='utf-8')
    
    print(f"[INFO] Loaded {len(processed_df)} processed rows")
    print(f"[INFO] From {len(original_df)} original transactions")
    
    # Filter for "no_delimiter" parsing method
    no_delimiter_df = processed_df[processed_df['parsing_method'] == 'no_delimiter']
    
    # Get unique transactions with no delimiter
    unique_transactions = no_delimiter_df['IG_ID'].unique()
    print(f"\n[STATISTICS]")
    print(f"Transactions processed with 'no_delimiter' method: {len(unique_transactions)}")
    
    # Analyze by investor count
    investor_counts = no_delimiter_df.groupby('IG_ID')['investor_count'].first().value_counts().sort_index()
    
    print(f"\n[DISTRIBUTION BY NUMBER OF INVESTORS]")
    for count, freq in investor_counts.items():
        print(f"  {count} investors: {freq} transactions")
    
    # Analyze role assignments
    print(f"\n[ROLE ASSIGNMENTS IN NO-DELIMITER CASES]")
    role_counts = no_delimiter_df['investor_role'].value_counts()
    print(f"  Lead roles: {role_counts.get('lead', 0)}")
    print(f"  Participant roles: {role_counts.get('participant', 0)}")
    
    # Show examples by investor count
    print(f"\n[EXAMPLES BY INVESTOR COUNT]")
    
    # 2 investors
    two_investor_ids = no_delimiter_df[no_delimiter_df['investor_count'] == 2]['IG_ID'].unique()
    if len(two_investor_ids) > 0:
        print(f"\n--- Cases with 2 investors (showing first 5) ---")
        for ig_id in two_investor_ids[:5]:
            transaction = no_delimiter_df[no_delimiter_df['IG_ID'] == ig_id].iloc[0]
            investors = no_delimiter_df[no_delimiter_df['IG_ID'] == ig_id]
            
            print(f"\nTarget: {transaction['Target name']}")
            print(f"Original: {transaction['Investors / Buyers']}")
            print(f"Parsed as:")
            for _, inv in investors.iterrows():
                print(f"  [{inv['investor_role']}] {inv['investor_name']}")
    
    # 3 investors
    three_investor_ids = no_delimiter_df[no_delimiter_df['investor_count'] == 3]['IG_ID'].unique()
    if len(three_investor_ids) > 0:
        print(f"\n--- Cases with 3 investors (showing first 5) ---")
        for ig_id in three_investor_ids[:5]:
            transaction = no_delimiter_df[no_delimiter_df['IG_ID'] == ig_id].iloc[0]
            investors = no_delimiter_df[no_delimiter_df['IG_ID'] == ig_id]
            
            print(f"\nTarget: {transaction['Target name']}")
            print(f"Original: {transaction['Investors / Buyers']}")
            print(f"Parsed as:")
            for _, inv in investors.iterrows():
                print(f"  [{inv['investor_role']}] {inv['investor_name']}")
    
    # 4+ investors
    many_investor_ids = no_delimiter_df[no_delimiter_df['investor_count'] >= 4]['IG_ID'].unique()
    if len(many_investor_ids) > 0:
        print(f"\n--- Cases with 4+ investors (showing first 5) ---")
        for ig_id in many_investor_ids[:5]:
            transaction = no_delimiter_df[no_delimiter_df['IG_ID'] == ig_id].iloc[0]
            investors = no_delimiter_df[no_delimiter_df['IG_ID'] == ig_id]
            
            print(f"\nTarget: {transaction['Target name']}")
            print(f"Original: {transaction['Investors / Buyers']}")
            print(f"Investor count: {transaction['investor_count']}")
            print(f"Parsed as:")
            for _, inv in investors.iterrows():
                print(f"  [{inv['investor_role']}] {inv['investor_name']}")
    
    # Find the maximum number of investors in no-delimiter cases
    max_investors = no_delimiter_df['investor_count'].max()
    max_investor_transaction = no_delimiter_df[no_delimiter_df['investor_count'] == max_investors].iloc[0]
    
    print(f"\n[MAXIMUM INVESTORS IN NO-DELIMITER CASE]")
    print(f"Maximum: {max_investors} investors")
    print(f"Target: {max_investor_transaction['Target name']}")
    print(f"Original: {max_investor_transaction['Investors / Buyers']}")
    
    # Summary
    print(f"\n[SUMMARY OF NO-DELIMITER HANDLING]")
    print(f"Current behavior: ALL investors marked as 'lead' when no delimiter present")
    print(f"Total affected transactions: {len(unique_transactions)}")
    print(f"Total affected investor rows: {len(no_delimiter_df)}")
    
    # Check if this is correct behavior
    print(f"\n[ANALYSIS]")
    print(f"When there's no (lead) or / delimiter, we assume:")
    print(f"  - All investors have equal status")
    print(f"  - All are marked as 'lead' investors")
    print(f"  - This affects {len(no_delimiter_df)} investor entries")
    
    # Suggestion
    print(f"\n[RECOMMENDATION]")
    print(f"For transactions with 4+ investors and no delimiter:")
    print(f"  - Current: All marked as 'lead'")
    print(f"  - Alternative 1: First investor as lead, rest as participants")
    print(f"  - Alternative 2: Manual review for large investor groups")
    print(f"  - Alternative 3: Keep current approach (all equal status)")
    
    return no_delimiter_df

if __name__ == "__main__":
    no_delimiter_cases = analyze_no_delimiter_cases()
    print(f"\n[COMPLETE] Analysis finished")