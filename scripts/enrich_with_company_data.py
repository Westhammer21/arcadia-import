#!/usr/bin/env python3
"""
Script to enrich unmapped transactions with Arcadia company data
Created: 2025-09-03
Purpose: Match Target names with company names/aliases and add company information
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import re

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
                name_index[name_norm].append((idx, 'name', row['name']))
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
                        name_index[aka_norm].append((idx, 'also_known_as', aka))
        
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
                        name_index[alias_norm].append((idx, 'aliases', alias))
    
    stats['total_mappings'] = len(name_index)
    
    print(f"   Total companies: {stats['total_companies']}")
    print(f"   Companies with name: {stats['with_name']}")
    print(f"   Companies with also_known_as: {stats['with_also_known_as']}")
    print(f"   Companies with aliases: {stats['with_aliases']}")
    print(f"   Total unique name mappings: {stats['total_mappings']}")
    
    # Check for multiple mappings (same normalized name -> multiple companies)
    multiple_mappings = {k: v for k, v in name_index.items() if len(v) > 1}
    if multiple_mappings:
        print(f"\n   WARNING: {len(multiple_mappings)} names map to multiple companies")
        # Show first 3 examples
        for name, mappings in list(multiple_mappings.items())[:3]:
            print(f"     '{name}' -> {len(mappings)} companies")
    
    return name_index, stats

def match_transactions(trans_df, company_df, name_index):
    """Match transaction target names with company data"""
    
    print("\n3. Matching target names")
    print("-" * 50)
    
    # Prepare columns with arc_ prefix
    company_columns = company_df.columns.tolist()
    prefixed_columns = {col: f'arc_{col}' for col in company_columns}
    
    # Initialize new columns in transaction dataframe
    for arc_col in prefixed_columns.values():
        trans_df[arc_col] = np.nan
    
    # Track matching results
    matches = []
    no_matches = []
    multiple_matches = []
    
    for idx, row in trans_df.iterrows():
        target_name = row['Target name']
        
        if pd.isna(target_name) or target_name == '':
            no_matches.append({
                'row': idx + 2,  # Excel row number
                'IG_ID': row['IG_ID'],
                'target_name': target_name,
                'reason': 'Empty target name'
            })
            continue
        
        # Normalize for matching
        target_norm = normalize_for_matching(target_name)
        
        if target_norm in name_index:
            mappings = name_index[target_norm]
            
            if len(mappings) == 1:
                # Single match - perfect!
                company_idx, match_field, original_value = mappings[0]
                company_row = company_df.iloc[company_idx]
                
                # Add all company columns with arc_ prefix
                for col, arc_col in prefixed_columns.items():
                    trans_df.at[idx, arc_col] = company_row[col]
                
                matches.append({
                    'row': idx + 2,
                    'IG_ID': row['IG_ID'],
                    'target_name': target_name,
                    'matched_with': original_value,
                    'match_field': match_field,
                    'company_id': company_row['id']
                })
            
            else:
                # Multiple matches - flag for review
                company_ids = []
                match_details = []
                
                for company_idx, match_field, original_value in mappings:
                    company_row = company_df.iloc[company_idx]
                    company_ids.append(str(company_row['id']))
                    match_details.append(f"{match_field}:{original_value}")
                
                multiple_matches.append({
                    'row': idx + 2,
                    'IG_ID': row['IG_ID'],
                    'target_name': target_name,
                    'normalized': target_norm,
                    'company_ids': ', '.join(company_ids),
                    'match_details': ' | '.join(match_details),
                    'match_count': len(mappings)
                })
        else:
            # No match found
            no_matches.append({
                'row': idx + 2,
                'IG_ID': row['IG_ID'],
                'target_name': target_name,
                'reason': 'No matching company found'
            })
    
    print(f"   Successful matches: {len(matches)}")
    print(f"   No matches: {len(no_matches)}")
    print(f"   Multiple matches: {len(multiple_matches)}")
    print(f"   Match rate: {len(matches)/len(trans_df)*100:.1f}%")
    
    return trans_df, matches, no_matches, multiple_matches

def create_matching_report(matches, no_matches, multiple_matches, output_dir):
    """Create detailed matching report in markdown format"""
    
    report_file = output_dir / 'TARGET_NAME_MATCHING_REPORT.md'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Target Name Matching Report\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Script**: enrich_with_company_data.py\n\n")
        
        f.write("## Summary Statistics\n\n")
        total = len(matches) + len(no_matches) + len(multiple_matches)
        f.write(f"- **Total transactions processed**: {total}\n")
        f.write(f"- **Successful matches**: {len(matches)} ({len(matches)/total*100:.1f}%)\n")
        f.write(f"- **No matches found**: {len(no_matches)} ({len(no_matches)/total*100:.1f}%)\n")
        f.write(f"- **Multiple matches (ambiguous)**: {len(multiple_matches)} ({len(multiple_matches)/total*100:.1f}%)\n\n")
        
        f.write("---\n\n")
        
        # Multiple matches section
        if multiple_matches:
            f.write("## ⚠️ Multiple Matches (Require Review)\n\n")
            f.write("These target names matched multiple companies and need manual review:\n\n")
            f.write("| Row | IG_ID | Target Name | Matched Companies | Details |\n")
            f.write("|-----|-------|-------------|-------------------|----------|\n")
            
            for item in multiple_matches[:20]:  # Show first 20
                f.write(f"| {item['row']} | {item['IG_ID']} | {item['target_name']} | "
                       f"{item['company_ids']} | {item['match_count']} matches |\n")
            
            if len(multiple_matches) > 20:
                f.write(f"\n*... and {len(multiple_matches)-20} more multiple matches*\n")
            
            f.write("\n---\n\n")
        
        # No matches section
        if no_matches:
            f.write("## ❌ No Matches Found\n\n")
            f.write("These target names could not be matched to any company:\n\n")
            f.write("| Row | IG_ID | Target Name | Reason |\n")
            f.write("|-----|-------|-------------|--------|\n")
            
            for item in no_matches[:50]:  # Show first 50
                target = item['target_name'] if item['target_name'] else '[empty]'
                f.write(f"| {item['row']} | {item['IG_ID']} | {target} | {item['reason']} |\n")
            
            if len(no_matches) > 50:
                f.write(f"\n*... and {len(no_matches)-50} more unmatched target names*\n")
            
            f.write("\n---\n\n")
        
        # Successful matches sample
        f.write("## ✅ Successful Matches (Sample)\n\n")
        f.write("First 20 successful matches for verification:\n\n")
        f.write("| Row | IG_ID | Target Name | Matched With | Match Field | Company ID |\n")
        f.write("|-----|-------|-------------|--------------|-------------|------------|\n")
        
        for item in matches[:20]:
            f.write(f"| {item['row']} | {item['IG_ID']} | {item['target_name']} | "
                   f"{item['matched_with']} | {item['match_field']} | {item['company_id']} |\n")
        
        f.write(f"\n*Total successful matches: {len(matches)}*\n")
    
    print(f"\n   Report saved: {report_file}")
    
    return report_file

def main():
    """Main execution function"""
    
    print("=" * 70)
    print("TARGET NAME ENRICHMENT WITH ARCADIA COMPANY DATA")
    print("=" * 70)
    
    # File paths
    trans_file = Path('../output/ig_arc_unmapped_final.csv')
    company_file = Path('../src/company-names-arcadia.csv')
    output_file = Path('../output/ig_arc_unmapped_enriched.csv')
    output_dir = Path('../output')
    
    # Load data
    print("\n1. Loading data files")
    print("-" * 50)
    
    print(f"   Loading transactions: {trans_file}")
    trans_df = pd.read_csv(trans_file, encoding='utf-8')
    print(f"   Loaded {len(trans_df)} unmapped transactions")
    
    print(f"   Loading company data: {company_file}")
    company_df = pd.read_csv(company_file, encoding='utf-8')
    print(f"   Loaded {len(company_df)} companies")
    
    # Build company name index
    name_index, index_stats = build_company_index(company_df)
    
    # Perform matching
    enriched_df, matches, no_matches, multiple_matches = match_transactions(
        trans_df.copy(), company_df, name_index
    )
    
    # Save enriched data
    print("\n4. Saving enriched data")
    print("-" * 50)
    print(f"   Output file: {output_file}")
    enriched_df.to_csv(output_file, index=False, encoding='utf-8')
    print("   File saved successfully!")
    
    # Create matching report
    print("\n5. Creating matching report")
    print("-" * 50)
    report_file = create_matching_report(matches, no_matches, multiple_matches, output_dir)
    
    # Final summary
    print("\n" + "=" * 70)
    print("ENRICHMENT COMPLETE!")
    print("=" * 70)
    print(f"\nResults:")
    print(f"  ✅ Successful matches: {len(matches)} ({len(matches)/len(trans_df)*100:.1f}%)")
    print(f"  ❌ No matches: {len(no_matches)} ({len(no_matches)/len(trans_df)*100:.1f}%)")
    print(f"  ⚠️  Multiple matches: {len(multiple_matches)} ({len(multiple_matches)/len(trans_df)*100:.1f}%)")
    print(f"\nOutput files:")
    print(f"  - Enriched data: {output_file}")
    print(f"  - Matching report: {report_file}")
    
    # Save detailed lists for further analysis
    if no_matches:
        no_match_file = output_dir / 'unmatched_target_names.csv'
        pd.DataFrame(no_matches).to_csv(no_match_file, index=False, encoding='utf-8')
        print(f"  - Unmatched list: {no_match_file}")
    
    if multiple_matches:
        multi_match_file = output_dir / 'multiple_match_target_names.csv'
        pd.DataFrame(multiple_matches).to_csv(multi_match_file, index=False, encoding='utf-8')
        print(f"  - Multiple matches: {multi_match_file}")
    
    return {
        'total': len(trans_df),
        'matched': len(matches),
        'unmatched': len(no_matches),
        'multiple': len(multiple_matches),
        'match_rate': len(matches)/len(trans_df)*100
    }

if __name__ == "__main__":
    results = main()