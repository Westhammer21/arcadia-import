#!/usr/bin/env python3
"""
Consolidate Perfect Matches with Full Details
==============================================
Creates a comprehensive comparison file with full details from both
InvestGame and Arcadia databases for the 175 perfect matches.

Author: Data Analytics Team
Date: 01-09-2025
"""

import pandas as pd
import numpy as np
from datetime import datetime

def load_and_process_data():
    """Load all required data files"""
    print("=" * 80)
    print("CONSOLIDATING PERFECT MATCHES WITH FULL DETAILS")
    print("=" * 80)
    
    # 1. Load perfect matches
    print("\n1. LOADING PERFECT MATCHES...")
    matches = pd.read_csv('output/perfect_matches_4_criteria.csv')
    print(f"   Loaded {len(matches)} perfect matches")
    
    # 2. Load InvestGame database
    print("\n2. LOADING INVESTGAME DATABASE...")
    ig = pd.read_csv('output/investgame_new.csv', encoding='utf-8')
    print(f"   Loaded {len(ig)} InvestGame transactions")
    
    # 3. Load Arcadia database
    print("\n3. LOADING ARCADIA DATABASE...")
    arc = pd.read_csv('output/arcadia_new.csv', encoding='utf-8')
    print(f"   Loaded {len(arc)} Arcadia transactions")
    
    return matches, ig, arc

def extract_investgame_details(matches, ig):
    """Extract relevant InvestGame details for matched IDs"""
    print("\n4. EXTRACTING INVESTGAME DETAILS...")
    
    # Select relevant columns from InvestGame
    ig_columns = [
        'IG_ID',
        'Date',
        'Target name',
        'Investors / Buyers',
        'Type',
        'Size, $m',
        'Deal Link'
    ]
    
    # Filter InvestGame data for matched IDs
    ig_filtered = ig[ig['IG_ID'].isin(matches['ig_id'])][ig_columns].copy()
    
    # Rename columns with IG_ prefix
    ig_filtered.columns = [
        'IG_ID',
        'IG_Date',
        'IG_Target_Name',
        'IG_Investors',
        'IG_Type',
        'IG_Size_M',
        'IG_Deal_Link'
    ]
    
    print(f"   Extracted details for {len(ig_filtered)} InvestGame transactions")
    return ig_filtered

def extract_arcadia_details(matches, arc):
    """Extract relevant Arcadia details for matched IDs"""
    print("\n5. EXTRACTING ARCADIA DETAILS...")
    
    # Select relevant columns from Arcadia
    arc_columns = [
        'ID',
        'Announcement date*',
        'Target Company',
        'Lead Investor / Acquirer',
        'Other Investors',
        'Transaction Type*',
        'Transaction Size*, $M',
        'Source URL*'
    ]
    
    # Filter Arcadia data for matched IDs
    arc_filtered = arc[arc['ID'].isin(matches['arc_id'])][arc_columns].copy()
    
    # Rename columns with Arc_ prefix
    arc_filtered.columns = [
        'Arc_ID',
        'Arc_Date',
        'Arc_Target_Company',
        'Arc_Lead_Investor',
        'Arc_Other_Investors',
        'Arc_Type',
        'Arc_Size_M',
        'Arc_Source_URL'
    ]
    
    print(f"   Extracted details for {len(arc_filtered)} Arcadia transactions")
    return arc_filtered

def merge_all_data(matches, ig_details, arc_details):
    """Merge all data into comprehensive comparison file"""
    print("\n6. MERGING ALL DATA...")
    
    # Start with matches data
    result = matches.copy()
    
    # Merge InvestGame details
    result = result.merge(
        ig_details,
        left_on='ig_id',
        right_on='IG_ID',
        how='left'
    )
    
    # Merge Arcadia details
    result = result.merge(
        arc_details,
        left_on='arc_id',
        right_on='Arc_ID',
        how='left'
    )
    
    # Select and reorder columns for better comparison
    comparison_columns = [
        # Match identifiers
        'arc_id',
        'ig_id',
        
        # Dates side by side
        'IG_Date',
        'Arc_Date',
        
        # Target names side by side
        'IG_Target_Name',
        'Arc_Target_Company',
        
        # Investors side by side
        'IG_Investors',
        'Arc_Lead_Investor',
        'Arc_Other_Investors',
        
        # Transaction types side by side
        'IG_Type',
        'Arc_Type',
        
        # Sizes side by side
        'IG_Size_M',
        'Arc_Size_M',
        
        # URLs side by side
        'IG_Deal_Link',
        'Arc_Source_URL',
        
        # Match quality scores
        'url_similarity',
        'company_similarity',
        'size_diff_pct'
    ]
    
    # Filter to only these columns
    result = result[comparison_columns]
    
    # Add a match number for easy reference
    result.insert(0, 'Match_Number', range(1, len(result) + 1))
    
    print(f"   Created consolidated file with {len(result)} matches")
    return result

def add_comparison_flags(df):
    """Add helpful comparison flags"""
    print("\n7. ADDING COMPARISON FLAGS...")
    
    # Flag exact matches
    df['Date_Match'] = df['IG_Date'] == df['Arc_Date']
    df['Size_Match'] = df['IG_Size_M'] == df['Arc_Size_M']
    df['Type_Match'] = df['IG_Type'] == df['Arc_Type']
    
    # Calculate investor overlap
    def check_investor_overlap(row):
        if pd.isna(row['IG_Investors']) or pd.isna(row['Arc_Lead_Investor']):
            return 'Unknown'
        
        ig_inv = str(row['IG_Investors']).lower()
        arc_lead = str(row['Arc_Lead_Investor']).lower()
        arc_other = str(row['Arc_Other_Investors']).lower() if not pd.isna(row['Arc_Other_Investors']) else ''
        
        if arc_lead in ig_inv or ig_inv in arc_lead:
            return 'Lead_Match'
        elif arc_other and (arc_other in ig_inv or ig_inv in arc_other):
            return 'Other_Match'
        else:
            return 'No_Match'
    
    df['Investor_Overlap'] = df.apply(check_investor_overlap, axis=1)
    
    print("   Added comparison flags for easier review")
    return df

def generate_summary_report(df):
    """Generate summary statistics"""
    print("\n8. SUMMARY STATISTICS...")
    print("-" * 70)
    
    # Count perfect alignments
    date_matches = df['Date_Match'].sum()
    size_matches = df['Size_Match'].sum()
    type_matches = df['Type_Match'].sum()
    
    print(f"   Date matches: {date_matches}/{len(df)} ({date_matches/len(df)*100:.1f}%)")
    print(f"   Size matches: {size_matches}/{len(df)} ({size_matches/len(df)*100:.1f}%)")
    print(f"   Type matches: {type_matches}/{len(df)} ({type_matches/len(df)*100:.1f}%)")
    
    # Investor overlap
    investor_stats = df['Investor_Overlap'].value_counts()
    print("\n   Investor overlap:")
    for status, count in investor_stats.items():
        print(f"     {status}: {count} ({count/len(df)*100:.1f}%)")
    
    # URL similarity stats
    avg_url_sim = df['url_similarity'].mean()
    print(f"\n   Average URL similarity: {avg_url_sim:.1f}%")
    
    # Company name similarity stats
    avg_company_sim = df['company_similarity'].mean()
    print(f"   Average company name similarity: {avg_company_sim:.1f}%")

def main():
    # Load all data
    matches, ig, arc = load_and_process_data()
    
    # Extract details from each database
    ig_details = extract_investgame_details(matches, ig)
    arc_details = extract_arcadia_details(matches, arc)
    
    # Merge all data
    consolidated = merge_all_data(matches, ig_details, arc_details)
    
    # Add comparison flags
    consolidated = add_comparison_flags(consolidated)
    
    # Generate summary
    generate_summary_report(consolidated)
    
    # Save the consolidated file
    print("\n9. SAVING CONSOLIDATED FILE...")
    output_file = 'output/perfect_matches_consolidated_details.csv'
    consolidated.to_csv(output_file, index=False, encoding='utf-8')
    print(f"   Saved to: {output_file}")
    
    # Create a simplified version for quick review
    print("\n10. CREATING SIMPLIFIED COMPARISON FILE...")
    simplified = consolidated[[
        'Match_Number',
        'IG_Date', 'Arc_Date',
        'IG_Target_Name', 'Arc_Target_Company',
        'IG_Size_M', 'Arc_Size_M',
        'IG_Type', 'Arc_Type',
        'Date_Match', 'Size_Match', 'Type_Match',
        'company_similarity'
    ]]
    
    simplified_file = 'output/perfect_matches_simple_comparison.csv'
    simplified.to_csv(simplified_file, index=False, encoding='utf-8')
    print(f"   Saved simplified version to: {simplified_file}")
    
    print("\n" + "=" * 80)
    print("CONSOLIDATION COMPLETE")
    print("=" * 80)
    print(f"\nCreated comprehensive comparison file with {len(consolidated)} perfect matches")
    print("Files created:")
    print(f"  - {output_file} (full details)")
    print(f"  - {simplified_file} (simplified for quick review)")

if __name__ == "__main__":
    main()