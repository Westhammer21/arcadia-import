#!/usr/bin/env python3
"""
Analyze and process Investors/Buyers column
============================================
Step 1: Identify simple vs complex investor cases
Step 2: Create ig_tier_lead_investor_acquirer column

Author: AI Analytics Team
Date: 2025-09-04
"""

import pandas as pd
import re
from pathlib import Path

def analyze_investor_patterns(df):
    """Analyze patterns in Investors/Buyers column"""
    
    print("\n" + "="*80)
    print("ANALYZING INVESTOR/BUYER PATTERNS")
    print("="*80)
    
    # Get the investors column
    investors_col = df['Investors / Buyers'].fillna('')
    
    # Define patterns for complex cases
    has_comma = investors_col.str.contains(',', na=False)
    has_slash = investors_col.str.contains('/', na=False)
    has_lead = investors_col.str.contains(r'\(lead\)', case=False, na=False)
    
    # Simple cases: no special characters (single investor)
    simple_cases = ~(has_comma | has_slash | has_lead)
    
    # Complex cases: has any of the special patterns
    complex_cases = has_comma | has_slash | has_lead
    
    print(f"\n[STATISTICS] TOTAL TRANSACTIONS: {len(df)}")
    print(f"\n[OK] SIMPLE CASES (single investor): {simple_cases.sum()} ({simple_cases.sum()/len(df)*100:.1f}%)")
    print(f"[COMPLEX] COMPLEX CASES (multiple investors): {complex_cases.sum()} ({complex_cases.sum()/len(df)*100:.1f}%)")
    
    # Breakdown of complex cases
    print(f"\n[BREAKDOWN] COMPLEX CASES BREAKDOWN:")
    print(f"   - Has comma (,): {has_comma.sum()}")
    print(f"   - Has slash (/): {has_slash.sum()}")
    print(f"   - Has '(lead)': {has_lead.sum()}")
    print(f"   - Has comma AND slash: {(has_comma & has_slash).sum()}")
    print(f"   - Has comma AND lead: {(has_comma & has_lead).sum()}")
    print(f"   - Has slash AND lead: {(has_slash & has_lead).sum()}")
    
    # Show examples
    print(f"\n[EXAMPLES] EXAMPLES OF SIMPLE CASES:")
    simple_examples = df[simple_cases]['Investors / Buyers'].head(5)
    for idx, example in enumerate(simple_examples, 1):
        print(f"   {idx}. {example}")
    
    print(f"\n[EXAMPLES] EXAMPLES OF COMPLEX CASES:")
    complex_examples = df[complex_cases]['Investors / Buyers'].head(10)
    for idx, example in enumerate(complex_examples, 1):
        print(f"   {idx}. {example}")
    
    return simple_cases, complex_cases

def create_lead_investor_column(df, simple_cases):
    """Create ig_tier_lead_investor_acquirer column for simple cases"""
    
    print("\n" + "="*80)
    print("CREATING LEAD INVESTOR/ACQUIRER COLUMN")
    print("="*80)
    
    # Initialize new column with empty values
    df['ig_tier_lead_investor_acquirer'] = ''
    
    # For simple cases, copy the investor name directly
    df.loc[simple_cases, 'ig_tier_lead_investor_acquirer'] = df.loc[simple_cases, 'Investors / Buyers']
    
    # Clean up any trailing/leading spaces
    df['ig_tier_lead_investor_acquirer'] = df['ig_tier_lead_investor_acquirer'].str.strip()
    
    print(f"[OK] Filled {simple_cases.sum()} simple cases with lead investor names")
    print(f"[PENDING] Left {(~simple_cases).sum()} complex cases empty (to be processed later)")
    
    # Show sample results
    print(f"\n[SAMPLE] SAMPLE RESULTS (Simple Cases):")
    sample = df[simple_cases][['Target name', 'Investors / Buyers', 'ig_tier_lead_investor_acquirer']].head(10)
    for idx, row in sample.iterrows():
        print(f"\n   Transaction: {row['Target name']}")
        print(f"   Original: {row['Investors / Buyers']}")
        print(f"   Lead Investor: {row['ig_tier_lead_investor_acquirer']}")
    
    return df

def main():
    """Main processing function"""
    
    # Load the data
    print("\n" + "="*80)
    print("LOADING DATA")
    print("="*80)
    
    base_path = Path(__file__).parent.parent
    input_path = base_path / 'output' / 'ig_arc_unmapped_vF.csv'
    
    # Read the CSV
    df = pd.read_csv(input_path, encoding='utf-8')
    print(f"[OK] Loaded {len(df)} unmapped transactions")
    
    # Analyze patterns
    simple_cases, complex_cases = analyze_investor_patterns(df)
    
    # Create lead investor column
    df = create_lead_investor_column(df, simple_cases)
    
    # Save the updated file
    output_path = base_path / 'output' / 'ig_arc_unmapped_investors_v1.csv'
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"\n[OK] Saved updated file to: {output_path}")
    
    # Summary statistics
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Total transactions: {len(df)}")
    print(f"Simple cases processed: {simple_cases.sum()}")
    print(f"Complex cases pending: {complex_cases.sum()}")
    print(f"Lead investors identified: {(df['ig_tier_lead_investor_acquirer'] != '').sum()}")
    
    return df, simple_cases, complex_cases

if __name__ == "__main__":
    df, simple_cases, complex_cases = main()