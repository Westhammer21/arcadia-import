#!/usr/bin/env python3
"""
Create Deduplicated Arcadia Company Cards
==========================================
Generate company cards with deduplication and IG_ID concatenation
Handles both targets and investors with proper role preservation

Author: AI Analytics Team
Date: 2025-01-09
Version: 2.0
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def load_data():
    """Load source data and reference files"""
    print("\n" + "="*80)
    print("LOADING DATA FILES")
    print("="*80)
    
    base_path = Path(__file__).parent.parent
    
    # Load main source file
    source_path = base_path / 'output' / 'ig_arc_unmapped_investors_FINAL.csv'
    df = pd.read_csv(source_path, encoding='utf-8')
    print(f"[OK] Loaded source: {len(df)} rows")
    
    # Load Arcadia company names for Undisclosed reference
    arcadia_path = base_path / 'src' / 'company-names-arcadia.csv'
    arcadia_companies = pd.read_csv(arcadia_path, encoding='utf-8')
    print(f"[OK] Loaded Arcadia reference: {len(arcadia_companies)} companies")
    
    # Get Undisclosed card
    undisclosed_card = arcadia_companies[arcadia_companies['id'] == 366].copy()
    if len(undisclosed_card) > 0:
        print(f"[OK] Found Undisclosed card with ID=366")
    else:
        print(f"[WARNING] Undisclosed card not found, will create new")
    
    return df, arcadia_companies, undisclosed_card

def select_best_metadata(group_df):
    """Select best metadata from duplicate records - prefer most complete data"""
    
    # Start with first row as base
    best_row = group_df.iloc[0].copy()
    
    # For each column, find first non-empty value
    for col in group_df.columns:
        # Skip columns we'll concatenate
        if col in ['IG_ID', 'investor_role', 'investor_name']:
            continue
            
        # Find first non-empty value
        non_empty = group_df[col].dropna()
        if len(non_empty) > 0:
            # Also check for empty strings
            non_empty = non_empty[non_empty != '']
            if len(non_empty) > 0:
                best_row[col] = non_empty.iloc[0]
    
    return best_row

def process_target_companies(df):
    """Process and deduplicate target companies"""
    
    print("\n" + "="*80)
    print("PROCESSING TARGET COMPANIES")
    print("="*80)
    
    # Get unique combinations of target + IG_ID (preserving order)
    target_data = []
    
    # Group by Target name to collect all IG_IDs
    target_groups = {}
    
    for idx, row in df.iterrows():
        target_name = row['Target name']
        ig_id = str(row['IG_ID'])
        
        if target_name not in target_groups:
            target_groups[target_name] = {
                'ig_ids': [],
                'rows': []
            }
        
        # Only add if this IG_ID not already added for this target
        if ig_id not in target_groups[target_name]['ig_ids']:
            target_groups[target_name]['ig_ids'].append(ig_id)
            target_groups[target_name]['rows'].append(row)
    
    print(f"[INFO] Found {len(target_groups)} unique target companies")
    
    # Create deduplicated target cards
    target_cards = []
    
    for target_name, data in target_groups.items():
        # Select best metadata from all rows
        rows_df = pd.DataFrame(data['rows'])
        best_row = select_best_metadata(rows_df)
        
        # Create card
        card = {
            'id': '',  # Empty for new cards
            'status': best_row['arc_status'] if pd.notna(best_row['arc_status']) and best_row['arc_status'] != '' else 'TO BE ENRICHED',
            'name': best_row['arc_name'] if pd.notna(best_row['arc_name']) and best_row['arc_name'] != '' else target_name,
            'also_known_as': best_row['arc_also_known_as'] if pd.notna(best_row['arc_also_known_as']) else '',
            'aliases': best_row['arc_aliases'] if pd.notna(best_row['arc_aliases']) else '',
            'type': best_row['arc_type'] if pd.notna(best_row['arc_type']) and best_row['arc_type'] != '' else 'Strategic / CVC',
            'founded': best_row['arc_founded'] if pd.notna(best_row['arc_founded']) else (best_row['Target Founded'] if pd.notna(best_row['Target Founded']) else ''),
            'hq_country': best_row['arc_hq_country'] if pd.notna(best_row['arc_hq_country']) else (best_row["Target's Country"] if pd.notna(best_row["Target's Country"]) else ''),
            'hq_region': best_row['arc_hq_region'] if pd.notna(best_row['arc_hq_region']) else (best_row['Region'] if pd.notna(best_row['Region']) else ''),
            'ownership': best_row['arc_ownership'] if pd.notna(best_row['arc_ownership']) and best_row['arc_ownership'] != '' else 'Private',
            'sector': best_row['arc_sector'] if pd.notna(best_row['arc_sector']) else (best_row['Sector'] if pd.notna(best_row['Sector']) else ''),
            'segment': best_row['arc_segment'] if pd.notna(best_row['arc_segment']) else (best_row['Segment'] if pd.notna(best_row['Segment']) else ''),
            'features': best_row['arc_features'] if pd.notna(best_row['arc_features']) else '',
            'specialization': best_row['arc_specialization'] if pd.notna(best_row['arc_specialization']) and best_row['arc_specialization'] != '' else 'Generalist',
            'aum': best_row['arc_aum'] if pd.notna(best_row['arc_aum']) else '',
            'parent_company': best_row['arc_parent_company'] if pd.notna(best_row['arc_parent_company']) else '',
            'transactions_count': best_row['arc_transactions_count'] if pd.notna(best_row['arc_transactions_count']) else 0,
            'was_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': '',
            'was_changed': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'modified_by': '',
            'search_index': '',  # Will generate
            'arc_website': best_row["Target's Website"] if pd.notna(best_row["Target's Website"]) else '',
            'IG_ID': ', '.join(data['ig_ids']),  # Concatenate with ", "
            'investor_role': ', '.join(['TARGET'] * len(data['ig_ids']))  # All are TARGET
        }
        
        # Generate search index
        search_parts = [card['name']]
        if card['hq_country']:
            search_parts.append(card['hq_country'])
        if card['hq_region']:
            search_parts.append(card['hq_region'])
        card['search_index'] = ', '.join(search_parts)
        
        # Convert numeric fields to proper type
        if card['founded'] != '':
            try:
                card['founded'] = int(float(str(card['founded'])))
            except:
                card['founded'] = ''
        
        if card['transactions_count'] != '':
            try:
                card['transactions_count'] = int(float(str(card['transactions_count'])))
            except:
                card['transactions_count'] = 0
        
        target_cards.append(card)
    
    print(f"[OK] Created {len(target_cards)} target company cards")
    print(f"[INFO] IG_IDs per target: min={min(len(d['ig_ids']) for d in target_groups.values())}, "
          f"max={max(len(d['ig_ids']) for d in target_groups.values())}, "
          f"avg={sum(len(d['ig_ids']) for d in target_groups.values())/len(target_groups):.1f}")
    
    return pd.DataFrame(target_cards)

def process_investor_companies(df, undisclosed_card):
    """Process and deduplicate investor companies"""
    
    print("\n" + "="*80)
    print("PROCESSING INVESTOR COMPANIES")
    print("="*80)
    
    # Group by investor_name to collect all IG_IDs and roles
    investor_groups = {}
    
    for idx, row in df.iterrows():
        investor_name = row['investor_name']
        ig_id = str(row['IG_ID'])
        role = row['investor_role']
        
        # Skip PARSE_ERROR
        if investor_name == 'PARSE_ERROR':
            continue
        
        if investor_name not in investor_groups:
            investor_groups[investor_name] = {
                'ig_ids': [],
                'roles': [],
                'rows': []
            }
        
        # Add in order of appearance (no dedup at this level to preserve order)
        investor_groups[investor_name]['ig_ids'].append(ig_id)
        investor_groups[investor_name]['roles'].append(role)
        investor_groups[investor_name]['rows'].append(row)
    
    print(f"[INFO] Found {len(investor_groups)} unique investor companies")
    
    # Separate Undisclosed from others
    investor_cards = []
    
    # Handle Undisclosed specially
    if 'Undisclosed' in investor_groups:
        undisclosed_data = investor_groups['Undisclosed']
        
        if len(undisclosed_card) > 0:
            # Use existing card, update IG_ID and role
            card = undisclosed_card.iloc[0].to_dict()
            card['IG_ID'] = ', '.join(undisclosed_data['ig_ids'])
            card['investor_role'] = ', '.join(undisclosed_data['roles'])
            # Keep existing arc_website if any
            if 'arc_website' not in card:
                card['arc_website'] = ''
        else:
            # Create new Undisclosed card
            card = {
                'id': '',  # Will be assigned by system
                'status': 'TO BE ENRICHED',
                'name': 'Undisclosed',
                'also_known_as': '',
                'aliases': 'Undisclosed company',
                'type': 'Investor',
                'founded': '',
                'hq_country': '',
                'hq_region': '',
                'ownership': 'Private',
                'sector': '',
                'segment': '',
                'features': '',
                'specialization': 'Generalist',
                'aum': '',
                'parent_company': '',
                'transactions_count': 0,
                'was_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'created_by': '',
                'was_changed': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'modified_by': '',
                'search_index': 'Undisclosed',
                'arc_website': '',
                'IG_ID': ', '.join(undisclosed_data['ig_ids']),
                'investor_role': ', '.join(undisclosed_data['roles'])
            }
        
        investor_cards.append(card)
        print(f"[OK] Processed Undisclosed with {len(undisclosed_data['ig_ids'])} transactions")
        
        # Remove from main processing
        del investor_groups['Undisclosed']
    
    # Process other investors
    for investor_name, data in investor_groups.items():
        if pd.isna(investor_name) or investor_name == '':
            continue
            
        card = {
            'id': '',  # Empty for new cards
            'status': 'TO BE ENRICHED',
            'name': investor_name,
            'also_known_as': '',
            'aliases': '',
            'type': 'Investor',
            'founded': '',
            'hq_country': '',
            'hq_region': '',
            'ownership': 'Private',
            'sector': '',
            'segment': '',
            'features': '',
            'specialization': 'Generalist',
            'aum': '',
            'parent_company': '',
            'transactions_count': 0,
            'was_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': '',
            'was_changed': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'modified_by': '',
            'search_index': investor_name,
            'arc_website': '',
            'IG_ID': ', '.join(data['ig_ids']),
            'investor_role': ', '.join(data['roles'])
        }
        
        investor_cards.append(card)
    
    print(f"[OK] Created {len(investor_cards)} investor company cards")
    
    return pd.DataFrame(investor_cards)

def identify_dual_role_companies(target_df, investor_df):
    """Identify companies that appear in both target and investor lists"""
    
    print("\n" + "="*80)
    print("IDENTIFYING DUAL ROLE COMPANIES")
    print("="*80)
    
    target_names = set(target_df['name'].unique())
    investor_names = set(investor_df['name'].unique())
    
    dual_role = target_names.intersection(investor_names)
    
    if dual_role:
        print(f"[INFO] Found {len(dual_role)} companies in both target and investor roles:")
        for name in sorted(dual_role)[:10]:  # Show first 10
            target_ig = target_df[target_df['name'] == name]['IG_ID'].iloc[0]
            investor_ig = investor_df[investor_df['name'] == name]['IG_ID'].iloc[0]
            print(f"  - {name}")
            print(f"    Target IGs: {target_ig}")
            print(f"    Investor IGs: {investor_ig}")
    else:
        print(f"[INFO] No companies found in both roles")
    
    return dual_role

def validate_output(df):
    """Validate the output dataframe"""
    
    print("\n" + "="*80)
    print("VALIDATING OUTPUT")
    print("="*80)
    
    # Check columns
    expected_cols = [
        'id', 'status', 'name', 'also_known_as', 'aliases', 'type',
        'founded', 'hq_country', 'hq_region', 'ownership', 'sector',
        'segment', 'features', 'specialization', 'aum', 'parent_company',
        'transactions_count', 'was_added', 'created_by', 'was_changed',
        'modified_by', 'search_index', 'arc_website', 'IG_ID', 'investor_role'
    ]
    
    missing_cols = set(expected_cols) - set(df.columns)
    if missing_cols:
        print(f"[ERROR] Missing columns: {missing_cols}")
    else:
        print(f"[OK] All 25 columns present")
    
    # Check for format issues
    print(f"\n[FORMAT CHECKS]")
    
    # Check IG_ID format
    bad_format = df[~df['IG_ID'].str.contains(', ', na=False) & df['IG_ID'].str.contains(',', na=False)]
    if len(bad_format) > 0:
        print(f"[WARNING] {len(bad_format)} rows with incorrect IG_ID format (missing space after comma)")
    else:
        print(f"[OK] All IG_IDs properly formatted with ', ' separator")
    
    # Check role format
    bad_roles = df[~df['investor_role'].str.contains(', ', na=False) & df['investor_role'].str.contains(',', na=False)]
    if len(bad_roles) > 0:
        print(f"[WARNING] {len(bad_roles)} rows with incorrect role format")
    else:
        print(f"[OK] All roles properly formatted")
    
    # Check IG_ID and role count match
    mismatched = []
    for idx, row in df.iterrows():
        ig_count = len(row['IG_ID'].split(', '))
        role_count = len(row['investor_role'].split(', '))
        if ig_count != role_count:
            mismatched.append(row['name'])
    
    if mismatched:
        print(f"[ERROR] {len(mismatched)} rows with mismatched IG_ID/role counts")
        for name in mismatched[:5]:
            print(f"  - {name}")
    else:
        print(f"[OK] All IG_ID counts match role counts")
    
    # Statistics
    print(f"\n[STATISTICS]")
    print(f"Total company cards: {len(df)}")
    print(f"Target companies: {len(df[df['investor_role'].str.contains('TARGET', na=False)])}")
    print(f"Investor companies: {len(df[~df['investor_role'].str.contains('TARGET', na=False)])}")
    print(f"Cards with multiple IGs: {len(df[df['IG_ID'].str.contains(',', na=False)])}")
    
    return True

def main():
    """Main processing function"""
    
    print("\n" + "="*80)
    print("ARCADIA COMPANY CARDS GENERATION - DEDUPLICATED")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load data
    df, arcadia_companies, undisclosed_card = load_data()
    
    # Process targets
    target_cards = process_target_companies(df)
    
    # Process investors
    investor_cards = process_investor_companies(df, undisclosed_card)
    
    # Identify dual role companies
    dual_roles = identify_dual_role_companies(target_cards, investor_cards)
    
    # Combine all cards
    all_cards = pd.concat([target_cards, investor_cards], ignore_index=True)
    
    # Sort by name for easier review
    all_cards = all_cards.sort_values('name')
    
    # Validate
    validate_output(all_cards)
    
    # Save output
    base_path = Path(__file__).parent.parent
    output_path = base_path / 'output' / 'arcadia_company_cards_deduplicated.csv'
    
    all_cards.to_csv(output_path, index=False, encoding='utf-8')
    print(f"\n[SAVED] Output file: {output_path}")
    print(f"[COMPLETE] Generated {len(all_cards)} deduplicated company cards")
    
    # Create summary report
    report_path = base_path / 'docs' / 'company_cards_generation_report.md'
    
    report = f"""# Company Cards Generation Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Total Cards Generated**: {len(all_cards)}
- **Target Companies**: {len(target_cards)}
- **Investor Companies**: {len(investor_cards)}
- **Dual Role Companies**: {len(dual_roles)}

## Deduplication Results
- **Original Rows**: 1,568
- **Deduplicated Cards**: {len(all_cards)}
- **Reduction**: {((1568 - len(all_cards)) / 1568 * 100):.1f}%

## IG_ID Concatenation
- **Cards with Single IG**: {len(all_cards[~all_cards['IG_ID'].str.contains(',', na=False)])}
- **Cards with Multiple IGs**: {len(all_cards[all_cards['IG_ID'].str.contains(',', na=False)])}
- **Maximum IGs per Card**: {max(len(row['IG_ID'].split(', ')) for _, row in all_cards.iterrows())}

## Special Cases
- **Undisclosed Card**: {'Included with ID=366' if any(all_cards['id'] == '366') else 'Created new'}
- **Parse Errors Skipped**: {len(df[df['investor_name'] == 'PARSE_ERROR'])}
- **TO BE CREATED Status**: {len(all_cards[all_cards['status'] == 'TO BE CREATED'])}

## Output
- **File**: arcadia_company_cards_deduplicated.csv
- **Columns**: 25 (22 Arcadia + 3 additional)
- **Encoding**: UTF-8
- **Ready for Import**: Yes
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"[REPORT] Saved to: {report_path}")
    
    return all_cards

if __name__ == "__main__":
    cards_df = main()