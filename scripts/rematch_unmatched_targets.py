#!/usr/bin/env python3
"""
Re-match unmatched target names after encoding fixes
Created: 2025-09-03
Purpose: Try to match target names that previously failed, now that encoding is fixed
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

def normalize_for_matching(text):
    """Normalize text for case-insensitive smart matching"""
    if pd.isna(text) or text == '':
        return ''
    
    # Convert to string and lowercase
    text = str(text).lower()
    
    # Remove extra spaces
    text = ' '.join(text.split())
    
    # Trim leading/trailing spaces
    text = text.strip()
    
    return text

def parse_comma_separated(value):
    """Parse comma-separated values from a field"""
    if pd.isna(value) or value == '':
        return []
    
    # Split by comma and clean each value
    values = str(value).split(',')
    return [v.strip() for v in values if v.strip()]

def build_company_index(company_df):
    """Build index mapping normalized names to company records"""
    
    print("\n2. Building company name index")
    print("-" * 50)
    
    # Dictionary to store normalized_name -> list of company indices
    name_index = {}
    
    # Statistics
    stats = {
        'total_companies': len(company_df),
        'with_name': 0,
        'with_also_known_as': 0,
        'with_aliases': 0,
        'total_mappings': 0
    }
    
    for idx, row in company_df.iterrows():
        company_id = row['id']
        
        # Process 'name' column
        if pd.notna(row['name']) and row['name']:
            name_norm = normalize_for_matching(row['name'])
            if name_norm:
                if name_norm not in name_index:
                    name_index[name_norm] = []
                name_index[name_norm].append((idx, 'name', row['name'], company_id))
                stats['with_name'] += 1
        
        # Process 'also_known_as' column
        if pd.notna(row['also_known_as']) and row['also_known_as']:
            also_known = parse_comma_separated(row['also_known_as'])
            if also_known:
                stats['with_also_known_as'] += 1
                for aka in also_known:
                    aka_norm = normalize_for_matching(aka)
                    if aka_norm:
                        if aka_norm not in name_index:
                            name_index[aka_norm] = []
                        name_index[aka_norm].append((idx, 'also_known_as', aka, company_id))
        
        # Process 'aliases' column
        if pd.notna(row['aliases']) and row['aliases']:
            aliases = parse_comma_separated(row['aliases'])
            if aliases:
                stats['with_aliases'] += 1
                for alias in aliases:
                    alias_norm = normalize_for_matching(alias)
                    if alias_norm:
                        if alias_norm not in name_index:
                            name_index[alias_norm] = []
                        name_index[alias_norm].append((idx, 'aliases', alias, company_id))
    
    stats['total_mappings'] = len(name_index)
    
    print(f"   Total companies: {stats['total_companies']}")
    print(f"   Total unique name mappings: {stats['total_mappings']}")
    
    return name_index, stats

def main():
    """Main execution function"""
    
    print("=" * 70)
    print("RE-MATCHING UNMATCHED TARGET NAMES AFTER ENCODING FIX")
    print("=" * 70)
    
    # File paths
    data_file = Path('../output/ig_arc_unmapped_FINAL_COMPLETE.csv')
    company_file = Path('../src/company-names-arcadia.csv')
    output_file = Path('../output/ig_arc_unmapped_FINAL_COMPLETE.csv')
    
    # Load data
    print("\n1. Loading data files")
    print("-" * 50)
    
    print(f"   Loading transactions: {data_file}")
    df = pd.read_csv(data_file, encoding='utf-8')
    print(f"   Loaded {len(df)} transactions")
    
    # Count how many are currently unmatched
    unmatched_mask = df['arc_id'].isna()
    unmatched_count = unmatched_mask.sum()
    print(f"   Currently unmatched: {unmatched_count} ({unmatched_count/len(df)*100:.1f}%)")
    
    if unmatched_count == 0:
        print("\n   All transactions already matched! No work needed.")
        return
    
    print(f"   Loading company data: {company_file}")
    company_df = pd.read_csv(company_file, encoding='utf-8')
    print(f"   Loaded {len(company_df)} companies")
    
    # Build company name index
    name_index, index_stats = build_company_index(company_df)
    
    # Prepare columns with arc_ prefix
    company_columns = company_df.columns.tolist()
    prefixed_columns = {col: f'arc_{col}' for col in company_columns}
    
    # Ensure all arc_ columns exist
    for arc_col in prefixed_columns.values():
        if arc_col not in df.columns:
            df[arc_col] = np.nan
    
    print("\n3. Attempting to match unmatched target names")
    print("-" * 50)
    
    # Track new matches
    new_matches = []
    still_unmatched = []
    
    # Special handling for Team 17
    TEAM_17_PREFERRED_ID = 163
    
    # Process only unmatched records
    for idx in df[unmatched_mask].index:
        target_name = df.at[idx, 'Target name']
        
        if pd.isna(target_name) or target_name == '':
            still_unmatched.append({
                'row': idx + 2,
                'IG_ID': df.at[idx, 'IG_ID'],
                'target_name': target_name,
                'reason': 'Empty target name'
            })
            continue
        
        # Normalize for matching
        target_norm = normalize_for_matching(target_name)
        
        if target_norm in name_index:
            mappings = name_index[target_norm]
            
            # Get unique company IDs
            unique_company_ids = list(set(m[3] for m in mappings))
            
            # Special handling for Team 17
            if "team 17" in target_norm:
                # Use the preferred ID for Team 17
                company_idx = None
                for m in mappings:
                    if m[3] == TEAM_17_PREFERRED_ID:
                        company_idx = m[0]
                        match_field = m[1]
                        original_value = m[2]
                        break
                
                if company_idx is not None:
                    company_row = company_df.iloc[company_idx]
                    # Add all company columns with arc_ prefix
                    for col, arc_col in prefixed_columns.items():
                        df.at[idx, arc_col] = company_row[col]
                    
                    new_matches.append({
                        'row': idx + 2,
                        'IG_ID': df.at[idx, 'IG_ID'],
                        'target_name': target_name,
                        'matched_with': original_value,
                        'match_field': match_field,
                        'company_id': TEAM_17_PREFERRED_ID
                    })
                continue
            
            if len(unique_company_ids) == 1:
                # Single company ID match
                company_id = unique_company_ids[0]
                # Get the first mapping for this company
                company_idx = mappings[0][0]
                match_field = mappings[0][1]
                original_value = mappings[0][2]
                
                company_row = company_df.iloc[company_idx]
                
                # Add all company columns with arc_ prefix
                for col, arc_col in prefixed_columns.items():
                    df.at[idx, arc_col] = company_row[col]
                
                new_matches.append({
                    'row': idx + 2,
                    'IG_ID': df.at[idx, 'IG_ID'],
                    'target_name': target_name,
                    'matched_with': original_value,
                    'match_field': match_field,
                    'company_id': company_id
                })
            else:
                # Multiple different companies - flag for review
                still_unmatched.append({
                    'row': idx + 2,
                    'IG_ID': df.at[idx, 'IG_ID'],
                    'target_name': target_name,
                    'reason': f'Multiple matches ({len(unique_company_ids)} companies)'
                })
        else:
            # No match found
            still_unmatched.append({
                'row': idx + 2,
                'IG_ID': df.at[idx, 'IG_ID'],
                'target_name': target_name,
                'reason': 'No matching company found'
            })
    
    print(f"   New matches found: {len(new_matches)}")
    print(f"   Still unmatched: {len(still_unmatched)}")
    
    # Show examples of new matches
    if new_matches:
        print("\n4. New matches found")
        print("-" * 50)
        for match in new_matches[:10]:
            print(f"   Row {match['row']}: '{match['target_name']}' -> Company ID {match['company_id']}")
            print(f"      Matched via: {match['match_field']} = '{match['matched_with']}'")
    
    # Show examples of still unmatched
    if still_unmatched:
        print("\n5. Sample still unmatched")
        print("-" * 50)
        for unmatch in still_unmatched[:10]:
            print(f"   Row {unmatch['row']}: '{unmatch['target_name']}' - {unmatch['reason']}")
    
    # Save updated file if new matches were found
    if new_matches:
        print("\n6. Saving updated file")
        print("-" * 50)
        print(f"   Output: {output_file}")
        df.to_csv(output_file, index=False, encoding='utf-8')
        print("   File saved successfully!")
        
        # Create report
        report_file = Path('../output/REMATCH_REPORT.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Target Name Re-matching Report\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**After**: Encoding fixes applied\n\n")
            
            f.write("## Summary\n\n")
            f.write(f"- **Previously unmatched**: {unmatched_count}\n")
            f.write(f"- **New matches found**: {len(new_matches)}\n")
            f.write(f"- **Still unmatched**: {len(still_unmatched)}\n")
            f.write(f"- **New match rate**: {len(new_matches)/unmatched_count*100:.1f}%\n\n")
            
            if new_matches:
                f.write("## New Matches Found\n\n")
                f.write("| Row | IG_ID | Target Name | Company ID | Match Field |\n")
                f.write("|-----|-------|-------------|------------|-------------|\n")
                for match in new_matches:
                    f.write(f"| {match['row']} | {match['IG_ID']} | {match['target_name']} | ")
                    f.write(f"{match['company_id']} | {match['match_field']} |\n")
            
            if still_unmatched:
                f.write("\n## Still Unmatched Target Names\n\n")
                f.write("| Row | IG_ID | Target Name | Reason |\n")
                f.write("|-----|-------|-------------|--------|\n")
                for unmatch in still_unmatched[:50]:
                    f.write(f"| {unmatch['row']} | {unmatch['IG_ID']} | ")
                    f.write(f"{unmatch['target_name']} | {unmatch['reason']} |\n")
                
                if len(still_unmatched) > 50:
                    f.write(f"\n*... and {len(still_unmatched)-50} more unmatched*\n")
        
        print(f"   Report saved: {report_file}")
    else:
        print("\n   No new matches found after encoding fixes.")
    
    # Final summary
    print("\n" + "=" * 70)
    print("RE-MATCHING COMPLETE!")
    print("=" * 70)
    
    # Calculate final statistics
    final_matched = df['arc_id'].notna().sum()
    print(f"\nFinal Statistics:")
    print(f"  Total transactions: {len(df)}")
    print(f"  Matched to companies: {final_matched} ({final_matched/len(df)*100:.1f}%)")
    print(f"  Unmatched: {len(df) - final_matched} ({(len(df) - final_matched)/len(df)*100:.1f}%)")
    
    if new_matches:
        print(f"\n  Improvement: +{len(new_matches)} matches (+{len(new_matches)/len(df)*100:.1f}% overall)")

if __name__ == "__main__":
    main()