#!/usr/bin/env python3
"""
Re-match target names for transactions with blank arc_id values
Created: 2025-09-03
Purpose: Match unmapped transactions to Arcadia companies after encoding fixes
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
from difflib import SequenceMatcher

def load_and_analyze_current_state():
    """Load current data and analyze blank arc_id records"""
    print("=" * 70)
    print("PHASE 1: ANALYZING CURRENT STATE")
    print("=" * 70)
    
    # Load the unmapped transactions
    input_file = Path('output/ig_arc_unmapped_FINAL_COMPLETE.csv')
    print(f"\n1. Loading data from: {input_file}")
    
    df = pd.read_csv(input_file, encoding='utf-8')
    total_records = len(df)
    print(f"   Total records: {total_records}")
    
    # Check arc_id column status
    if 'arc_id' not in df.columns:
        print("   WARNING: arc_id column not found!")
        return df, None, None
    
    # Count blank arc_id values (handle NaN, empty strings, etc.)
    blank_mask = df['arc_id'].isna() | (df['arc_id'].astype(str).str.strip() == '') | (df['arc_id'].astype(str) == 'nan')
    blank_count = blank_mask.sum()
    filled_count = total_records - blank_count
    
    print(f"\n2. Arc_id Status:")
    print(f"   - Filled arc_id: {filled_count} ({filled_count/total_records*100:.1f}%)")
    print(f"   - Blank arc_id: {blank_count} ({blank_count/total_records*100:.1f}%)")
    
    # Extract records with blank arc_id
    blank_records = df[blank_mask].copy()
    
    # Analyze target names in blank records
    print(f"\n3. Target Names in Blank Records:")
    unique_targets = blank_records['Target name'].nunique()
    print(f"   - Unique target names to match: {unique_targets}")
    
    # Sample of unmatched names
    print(f"\n   Sample of unmatched target names:")
    for name in blank_records['Target name'].head(10).values:
        print(f"   - {name}")
    
    return df, blank_records, blank_mask

def load_arcadia_companies():
    """Load Arcadia company reference data"""
    print("\n" + "=" * 70)
    print("PHASE 2: LOADING ARCADIA COMPANY REFERENCE DATA")
    print("=" * 70)
    
    # Load Arcadia companies
    arcadia_file = Path('src/company-names-arcadia.csv')
    print(f"\n1. Loading Arcadia companies from: {arcadia_file}")
    
    if not arcadia_file.exists():
        print(f"   ERROR: File not found: {arcadia_file}")
        return None
    
    arcadia_df = pd.read_csv(arcadia_file, encoding='utf-8')
    print(f"   Total Arcadia companies: {len(arcadia_df)}")
    
    # Display columns
    print(f"\n2. Available columns for matching:")
    for col in arcadia_df.columns:
        non_null = arcadia_df[col].notna().sum()
        print(f"   - {col}: {non_null} non-null values")
    
    return arcadia_df

def normalize_name(name):
    """Normalize company name for matching"""
    if pd.isna(name):
        return ""
    
    name = str(name)
    # Convert to lowercase
    name = name.lower()
    # Remove common suffixes
    suffixes = [' ltd', ' limited', ' inc', ' incorporated', ' llc', ' plc', ' corp', ' corporation',
                ' gmbh', ' ag', ' sa', ' srl', ' bv', ' nv', ' pty', ' pvt', ' co.', ' company']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    # Strip and remove extra spaces
    name = ' '.join(name.split())
    return name.strip()

def calculate_similarity(str1, str2):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, str1, str2).ratio()

def match_companies(blank_records, arcadia_df):
    """Match blank records to Arcadia companies"""
    print("\n" + "=" * 70)
    print("PHASE 3: MATCHING TARGET NAMES TO ARCADIA COMPANIES")
    print("=" * 70)
    
    matches = []
    no_matches = []
    
    # Create normalized lookup dictionary from Arcadia
    print("\n1. Building Arcadia lookup dictionary...")
    arcadia_lookup = {}
    
    for idx, row in arcadia_df.iterrows():
        # Primary name
        if pd.notna(row.get('name')):
            normalized = normalize_name(row['name'])
            if normalized and normalized not in arcadia_lookup:
                arcadia_lookup[normalized] = {
                    'id': row.get('id'),
                    'original_name': row.get('name'),
                    'match_type': 'primary_name'
                }
        
        # Also known as
        if pd.notna(row.get('also_known_as')):
            also_known = str(row['also_known_as'])
            for alt_name in also_known.split(','):
                normalized = normalize_name(alt_name.strip())
                if normalized and normalized not in arcadia_lookup:
                    arcadia_lookup[normalized] = {
                        'id': row.get('id'),
                        'original_name': row.get('name'),
                        'match_type': 'also_known_as'
                    }
        
        # Aliases
        if pd.notna(row.get('aliases')):
            aliases = str(row['aliases'])
            for alias in aliases.split(','):
                normalized = normalize_name(alias.strip())
                if normalized and normalized not in arcadia_lookup:
                    arcadia_lookup[normalized] = {
                        'id': row.get('id'),
                        'original_name': row.get('name'),
                        'match_type': 'alias'
                    }
    
    print(f"   Created lookup with {len(arcadia_lookup)} normalized entries")
    
    # Match each blank record
    print(f"\n2. Matching {len(blank_records)} records...")
    
    for idx, row in blank_records.iterrows():
        target_name = row['Target name']
        normalized_target = normalize_name(target_name)
        
        match_found = False
        
        # Try exact match first
        if normalized_target in arcadia_lookup:
            match_info = arcadia_lookup[normalized_target]
            matches.append({
                'index': idx,
                'target_name': target_name,
                'matched_id': match_info['id'],
                'matched_name': match_info['original_name'],
                'match_type': match_info['match_type'],
                'confidence': 'exact'
            })
            match_found = True
        
        # If no exact match, try fuzzy matching (only for high confidence)
        if not match_found and normalized_target:
            best_match = None
            best_score = 0
            
            for arc_name, arc_info in arcadia_lookup.items():
                score = calculate_similarity(normalized_target, arc_name)
                if score > best_score and score >= 0.9:  # 90% threshold
                    best_score = score
                    best_match = arc_info
            
            if best_match:
                matches.append({
                    'index': idx,
                    'target_name': target_name,
                    'matched_id': best_match['id'],
                    'matched_name': best_match['original_name'],
                    'match_type': f"fuzzy_{best_match['match_type']}",
                    'confidence': f"fuzzy_{best_score:.2f}"
                })
                match_found = True
        
        if not match_found:
            no_matches.append({
                'index': idx,
                'target_name': target_name
            })
    
    print(f"\n3. Matching Results:")
    print(f"   - Successful matches: {len(matches)}")
    print(f"   - No matches found: {len(no_matches)}")
    
    # Show match type breakdown
    if matches:
        match_df = pd.DataFrame(matches)
        print(f"\n4. Match Type Breakdown:")
        for match_type in match_df['match_type'].unique():
            count = (match_df['match_type'] == match_type).sum()
            print(f"   - {match_type}: {count}")
    
    return matches, no_matches

def update_dataframe(df, matches):
    """Update the dataframe with new arc_id values"""
    print("\n" + "=" * 70)
    print("PHASE 4: UPDATING DATAFRAME WITH MATCHES")
    print("=" * 70)
    
    updates_made = 0
    
    for match in matches:
        idx = match['index']
        new_id = match['matched_id']
        
        # Only update if currently blank
        current_value = df.at[idx, 'arc_id']
        if pd.isna(current_value) or str(current_value).strip() == '' or str(current_value) == 'nan':
            df.at[idx, 'arc_id'] = new_id
            updates_made += 1
    
    print(f"\n   Updated {updates_made} records with new arc_id values")
    
    return df, updates_made

def generate_report(matches, no_matches, updates_made, original_blank_count):
    """Generate comprehensive matching report"""
    print("\n" + "=" * 70)
    print("PHASE 5: GENERATING REPORT")
    print("=" * 70)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = Path(f'output/REMATCH_REPORT_{timestamp}.md')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# Target Name Re-matching Report\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Purpose**: Re-match target names for transactions with blank arc_id values\n\n")
        
        f.write(f"## Summary\n")
        f.write(f"- Original blank arc_id records: {original_blank_count}\n")
        f.write(f"- Successful matches: {len(matches)}\n")
        f.write(f"- No matches found: {len(no_matches)}\n")
        f.write(f"- Records updated: {updates_made}\n")
        f.write(f"- Match rate: {len(matches)/original_blank_count*100:.1f}%\n\n")
        
        if matches:
            f.write(f"## Successful Matches\n\n")
            f.write(f"### By Match Type\n")
            match_df = pd.DataFrame(matches)
            for match_type in sorted(match_df['match_type'].unique()):
                subset = match_df[match_df['match_type'] == match_type]
                f.write(f"- {match_type}: {len(subset)} matches\n")
            
            f.write(f"\n### Sample Matches (First 20)\n")
            f.write(f"| Target Name | Matched Name | Arc ID | Match Type | Confidence |\n")
            f.write(f"|-------------|--------------|--------|------------|------------|\n")
            for match in matches[:20]:
                f.write(f"| {match['target_name']} | {match['matched_name']} | ")
                f.write(f"{match['matched_id']} | {match['match_type']} | {match['confidence']} |\n")
        
        if no_matches:
            f.write(f"\n## Unmatched Records\n")
            f.write(f"Total: {len(no_matches)} records\n\n")
            f.write(f"### Sample Unmatched Names (First 20)\n")
            for record in no_matches[:20]:
                f.write(f"- {record['target_name']}\n")
    
    print(f"\n   Report saved to: {report_file}")
    return report_file

def main():
    """Main execution function"""
    print("\n" + "=" * 80)
    print(" TARGET NAME RE-MATCHING FOR BLANK ARC_ID RECORDS ")
    print("=" * 80)
    
    # Phase 1: Analyze current state
    df, blank_records, blank_mask = load_and_analyze_current_state()
    if blank_records is None or len(blank_records) == 0:
        print("\nNo blank arc_id records found. Exiting.")
        return
    
    original_blank_count = len(blank_records)
    
    # Phase 2: Load Arcadia companies
    arcadia_df = load_arcadia_companies()
    if arcadia_df is None:
        print("\nFailed to load Arcadia companies. Exiting.")
        return
    
    # Create backup
    print("\nCreating backup of current data...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = Path(f'output/ig_arc_unmapped_BACKUP_{timestamp}.csv')
    df.to_csv(backup_file, index=False, encoding='utf-8')
    print(f"   Backup saved to: {backup_file}")
    
    # Phase 3: Match companies
    matches, no_matches = match_companies(blank_records, arcadia_df)
    
    # Phase 4: Update dataframe
    df_updated, updates_made = update_dataframe(df, matches)
    
    # Phase 5: Save updated data
    output_file = Path('output/ig_arc_unmapped_FINAL_COMPLETE.csv')
    df_updated.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n   Updated data saved to: {output_file}")
    
    # Phase 6: Generate report
    report_file = generate_report(matches, no_matches, updates_made, original_blank_count)
    
    # Final statistics
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"\n✓ Processed {original_blank_count} records with blank arc_id")
    print(f"✓ Found {len(matches)} matches ({len(matches)/original_blank_count*100:.1f}%)")
    print(f"✓ Updated {updates_made} records")
    print(f"✓ {len(no_matches)} records remain unmatched")
    
    # Verify final state
    df_final = pd.read_csv(output_file, encoding='utf-8')
    final_blank = df_final['arc_id'].isna() | (df_final['arc_id'].astype(str).str.strip() == '') | (df_final['arc_id'].astype(str) == 'nan')
    final_blank_count = final_blank.sum()
    print(f"\nFinal blank arc_id count: {final_blank_count} (reduced by {original_blank_count - final_blank_count})")

if __name__ == "__main__":
    main()