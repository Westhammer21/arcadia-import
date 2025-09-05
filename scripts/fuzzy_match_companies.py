"""
Advanced Fuzzy Matching for Company IDs
Phase 1: Smart normalization matching (ignore case, spaces, punctuation)
Phase 2: Fuzzy matching with 95% threshold for minor typos
Updates TO BE CREATED companies if they match existing ones
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re
from difflib import SequenceMatcher
import json

def normalize_for_matching(text):
    """
    Normalize text for smart matching:
    - Lowercase
    - Remove punctuation and special characters
    - Replace & with and
    - Remove extra spaces
    - Remove common suffixes
    """
    if pd.isna(text) or text == '':
        return ''
    
    text = str(text).lower()
    
    # Replace special cases
    text = text.replace('&', ' and ')
    text = text.replace("'s", 's')
    text = text.replace("'", '')
    text = text.replace('-', ' ')
    text = text.replace('.', ' ')
    text = text.replace(',', ' ')
    text = text.replace('(', ' ')
    text = text.replace(')', ' ')
    text = text.replace('[', ' ')
    text = text.replace(']', ' ')
    text = text.replace('/', ' ')
    text = text.replace('\\', ' ')
    
    # Remove common suffixes for matching
    suffixes = [
        ' inc', ' incorporated', ' corp', ' corporation', ' llc', ' ltd', ' limited',
        ' company', ' co', ' plc', ' gmbh', ' ag', ' sa', ' srl', ' bv', ' nv',
        ' studios', ' studio', ' games', ' game', ' interactive', ' entertainment',
        ' digital', ' media', ' group', ' holdings', ' international', ' global'
    ]
    
    for suffix in suffixes:
        if text.endswith(suffix):
            text = text[:-len(suffix)]
    
    # Remove multiple spaces
    text = ' '.join(text.split())
    
    # Remove all remaining non-alphanumeric except spaces
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # Final cleanup
    text = ' '.join(text.split()).strip()
    
    return text

def calculate_fuzzy_score(str1, str2):
    """
    Calculate fuzzy matching score between two strings
    Returns score from 0 to 100
    """
    if not str1 or not str2:
        return 0
    
    # For very short strings (2-3 chars), require exact match
    if len(str1) <= 3 or len(str2) <= 3:
        return 100 if str1 == str2 else 0
    
    # Use SequenceMatcher for fuzzy matching
    return SequenceMatcher(None, str1, str2).ratio() * 100

def load_data():
    """Load unmapped companies and Arcadia database"""
    print("[LOAD] Loading data files...")
    
    unmapped_df = pd.read_csv('output/arcadia_company_unmapped.csv')
    arcadia_df = pd.read_csv('src/company-names-arcadia.csv')
    
    print(f"  - Loaded {len(unmapped_df)} unmapped companies")
    print(f"  - Companies without IDs: {unmapped_df['id'].isna().sum()}")
    print(f"  - Loaded {len(arcadia_df)} Arcadia companies")
    
    return unmapped_df, arcadia_df

def build_normalized_indexes(arcadia_df):
    """Build normalized lookup dictionaries for Phase 1"""
    print("\n[BUILD] Creating normalized matching indexes...")
    
    norm_to_ids = {}  # normalized name -> list of (id, original_name, field)
    
    for _, row in arcadia_df.iterrows():
        arc_id = row['id']
        
        # Normalize name
        if pd.notna(row['name']) and row['name'] != '':
            norm = normalize_for_matching(row['name'])
            if norm:
                if norm not in norm_to_ids:
                    norm_to_ids[norm] = []
                norm_to_ids[norm].append({
                    'id': arc_id,
                    'original': row['name'],
                    'field': 'name',
                    'row': row
                })
        
        # Normalize also_known_as
        if pd.notna(row['also_known_as']) and row['also_known_as'] != '':
            norm = normalize_for_matching(row['also_known_as'])
            if norm:
                if norm not in norm_to_ids:
                    norm_to_ids[norm] = []
                norm_to_ids[norm].append({
                    'id': arc_id,
                    'original': row['also_known_as'],
                    'field': 'also_known_as',
                    'row': row
                })
        
        # Normalize aliases (comma-separated)
        if pd.notna(row['aliases']) and row['aliases'] != '':
            aliases = str(row['aliases']).split(',')
            for alias in aliases:
                norm = normalize_for_matching(alias.strip())
                if norm:
                    if norm not in norm_to_ids:
                        norm_to_ids[norm] = []
                    norm_to_ids[norm].append({
                        'id': arc_id,
                        'original': alias.strip(),
                        'field': 'aliases',
                        'row': row
                    })
    
    print(f"  - Built normalized index with {len(norm_to_ids)} unique entries")
    
    return norm_to_ids

def phase1_smart_matching(unmapped_df, norm_to_ids):
    """Phase 1: Smart matching using normalization"""
    print("\n[PHASE 1] Smart Matching (normalized)...")
    
    matches = []
    multiple_matches = []
    
    for idx, row in unmapped_df.iterrows():
        if pd.notna(row['id']):
            continue  # Skip if already has ID
        
        company_name = row['name']
        normalized = normalize_for_matching(company_name)
        
        if normalized in norm_to_ids:
            candidates = norm_to_ids[normalized]
            
            if len(candidates) == 1:
                # Single match
                match_info = candidates[0]
                matches.append({
                    'unmapped_idx': idx,
                    'unmapped_name': company_name,
                    'unmapped_status': row['status'],
                    'matched_id': match_info['id'],
                    'matched_name': match_info['original'],
                    'match_field': match_info['field'],
                    'match_type': 'smart_normalization',
                    'score': 100,
                    'arcadia_row': match_info['row']
                })
            else:
                # Multiple matches - need review
                multiple_matches.append({
                    'unmapped_name': company_name,
                    'unmapped_status': row['status'],
                    'normalized': normalized,
                    'candidates': candidates
                })
    
    print(f"  - Found {len(matches)} single matches")
    print(f"  - Found {len(multiple_matches)} cases with multiple candidates")
    
    return matches, multiple_matches

def phase2_fuzzy_matching(unmapped_df, arcadia_df, existing_matches):
    """Phase 2: Fuzzy matching for remaining companies"""
    print("\n[PHASE 2] Fuzzy Matching (95% threshold)...")
    
    # Get indices of already matched companies
    matched_indices = {m['unmapped_idx'] for m in existing_matches}
    
    fuzzy_matches = []
    fuzzy_multiple = []
    
    # Pre-normalize all Arcadia names for faster comparison
    arcadia_normalized = {}
    for _, arc_row in arcadia_df.iterrows():
        arc_id = arc_row['id']
        
        names_to_check = []
        if pd.notna(arc_row['name']):
            names_to_check.append(('name', arc_row['name']))
        if pd.notna(arc_row['also_known_as']):
            names_to_check.append(('also_known_as', arc_row['also_known_as']))
        if pd.notna(arc_row['aliases']):
            for alias in str(arc_row['aliases']).split(','):
                names_to_check.append(('aliases', alias.strip()))
        
        for field, original in names_to_check:
            norm = normalize_for_matching(original)
            if norm:
                if norm not in arcadia_normalized:
                    arcadia_normalized[norm] = []
                arcadia_normalized[norm].append({
                    'id': arc_id,
                    'original': original,
                    'field': field,
                    'row': arc_row
                })
    
    # Check each unmapped company
    for idx, row in unmapped_df.iterrows():
        if pd.notna(row['id']) or idx in matched_indices:
            continue  # Skip if already has ID or matched in Phase 1
        
        company_name = row['name']
        normalized = normalize_for_matching(company_name)
        
        if not normalized:
            continue
        
        # Find fuzzy matches
        candidates = []
        for arc_norm, arc_entries in arcadia_normalized.items():
            score = calculate_fuzzy_score(normalized, arc_norm)
            
            if score >= 95:
                for entry in arc_entries:
                    candidates.append({
                        'id': entry['id'],
                        'original': entry['original'],
                        'field': entry['field'],
                        'score': score,
                        'row': entry['row']
                    })
        
        if candidates:
            # Sort by score
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
            # Get unique IDs
            unique_ids = list({c['id'] for c in candidates})
            
            if len(unique_ids) == 1:
                # Single company match (might have matched on multiple fields)
                best = candidates[0]
                fuzzy_matches.append({
                    'unmapped_idx': idx,
                    'unmapped_name': company_name,
                    'unmapped_status': row['status'],
                    'matched_id': best['id'],
                    'matched_name': best['original'],
                    'match_field': best['field'],
                    'match_type': 'fuzzy',
                    'score': best['score'],
                    'arcadia_row': best['row']
                })
            else:
                # Multiple companies matched
                fuzzy_multiple.append({
                    'unmapped_idx': idx,
                    'unmapped_name': company_name,
                    'unmapped_status': row['status'],
                    'candidates': candidates[:5]  # Top 5 candidates
                })
    
    print(f"  - Found {len(fuzzy_matches)} fuzzy matches")
    print(f"  - Found {len(fuzzy_multiple)} cases with multiple candidates")
    
    return fuzzy_matches, fuzzy_multiple

def update_matched_companies(unmapped_df, all_matches):
    """Update matched companies with Arcadia data"""
    print("\n[UPDATE] Updating matched companies...")
    
    updated_count = 0
    to_be_created_updated = 0
    
    for match in all_matches:
        idx = match['unmapped_idx']
        arc_row = match['arcadia_row']
        
        # Update ID
        unmapped_df.at[idx, 'id'] = arc_row['id']
        
        # If TO BE CREATED, update status and other fields
        if unmapped_df.at[idx, 'status'] == 'TO BE CREATED':
            to_be_created_updated += 1
            
            # Update status from Arcadia
            if pd.notna(arc_row.get('status')):
                unmapped_df.at[idx, 'status'] = arc_row['status']
            else:
                unmapped_df.at[idx, 'status'] = 'IMPORTED'
            
            # Update other fields if they're empty in unmapped but exist in Arcadia
            fields_to_update = [
                'also_known_as', 'aliases', 'type', 'founded', 'hq_country',
                'hq_region', 'ownership', 'sector', 'segment', 'features',
                'specialization', 'aum', 'parent_company', 'transactions_count'
            ]
            
            for field in fields_to_update:
                if field in arc_row and pd.notna(arc_row[field]):
                    if field not in unmapped_df.columns or pd.isna(unmapped_df.at[idx, field]):
                        unmapped_df.at[idx, field] = arc_row[field]
        
        updated_count += 1
    
    print(f"  - Updated {updated_count} companies with IDs")
    print(f"  - Converted {to_be_created_updated} TO BE CREATED companies")
    
    return unmapped_df

def generate_reports(all_matches, multiple_matches, fuzzy_multiple, unmapped_df):
    """Generate detailed reports"""
    print("\n[REPORT] Generating reports...")
    
    # Multiple matches report
    if multiple_matches or fuzzy_multiple:
        report = "# Companies with Multiple Matches - Manual Review Required\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if multiple_matches:
            report += "## Phase 1: Smart Matching - Multiple Exact Normalized Matches\n\n"
            for item in multiple_matches[:20]:  # First 20
                report += f"### {item['unmapped_name']} (Status: {item['unmapped_status']})\n"
                report += f"Normalized: `{item['normalized']}`\n\n"
                report += "| Arcadia ID | Company Name | Match Field |\n"
                report += "|------------|--------------|-------------|\n"
                for cand in item['candidates'][:5]:
                    report += f"| {cand['id']} | {cand['original']} | {cand['field']} |\n"
                report += "\n"
        
        if fuzzy_multiple:
            report += "## Phase 2: Fuzzy Matching - Multiple Companies Above 95%\n\n"
            for item in fuzzy_multiple[:20]:  # First 20
                report += f"### {item['unmapped_name']} (Status: {item['unmapped_status']})\n\n"
                report += "| Score | Arcadia ID | Company Name | Match Field |\n"
                report += "|-------|------------|--------------|-------------|\n"
                for cand in item['candidates']:
                    report += f"| {cand['score']:.1f}% | {cand['id']} | {cand['original']} | {cand['field']} |\n"
                report += "\n"
        
        with open('docs/multiple_matches_review.md', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"  - Multiple matches report saved: docs/multiple_matches_review.md")
    
    # Summary report
    summary = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_companies': int(len(unmapped_df)),
        'companies_without_id_before': int(unmapped_df['id'].isna().sum() + len(all_matches)),
        'phase1_matches': len([m for m in all_matches if m['match_type'] == 'smart_normalization']),
        'phase2_matches': len([m for m in all_matches if m['match_type'] == 'fuzzy']),
        'total_matched': len(all_matches),
        'multiple_matches_phase1': len(multiple_matches),
        'multiple_matches_phase2': len(fuzzy_multiple),
        'companies_without_id_after': int(unmapped_df['id'].isna().sum()),
        'to_be_created_converted': len([m for m in all_matches if m['unmapped_status'] == 'TO BE CREATED'])
    }
    
    with open('output/fuzzy_matching_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Detailed match log
    match_log_df = pd.DataFrame(all_matches)
    if len(match_log_df) > 0:
        match_log_df = match_log_df[['unmapped_name', 'unmapped_status', 'matched_id', 
                                     'matched_name', 'match_field', 'match_type', 'score']]
        match_log_df.to_csv('output/fuzzy_match_log.csv', index=False)
        print(f"  - Match log saved: output/fuzzy_match_log.csv")
    
    return summary

def main():
    print("[START] Advanced Fuzzy Matching Process")
    print("=" * 60)
    
    # Load data
    unmapped_df, arcadia_df = load_data()
    
    # Phase 1: Smart normalization matching
    norm_to_ids = build_normalized_indexes(arcadia_df)
    phase1_matches, multiple_matches = phase1_smart_matching(unmapped_df, norm_to_ids)
    
    # Phase 2: Fuzzy matching
    fuzzy_matches, fuzzy_multiple = phase2_fuzzy_matching(unmapped_df, arcadia_df, phase1_matches)
    
    # Combine all matches
    all_matches = phase1_matches + fuzzy_matches
    print(f"\n[COMBINE] Total matches found: {len(all_matches)}")
    
    # Update matched companies
    unmapped_df = update_matched_companies(unmapped_df, all_matches)
    
    # Save updated file
    output_file = 'output/arcadia_company_unmapped.csv'
    unmapped_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n[SAVE] Updated file saved: {output_file}")
    
    # Generate reports
    summary = generate_reports(all_matches, multiple_matches, fuzzy_multiple, unmapped_df)
    
    # Final summary
    print("\n" + "=" * 60)
    print("[SUCCESS] Fuzzy matching complete!")
    print(f"  Phase 1 (Smart): {summary['phase1_matches']} matches")
    print(f"  Phase 2 (Fuzzy): {summary['phase2_matches']} matches")
    print(f"  Total matched: {summary['total_matched']}")
    print(f"  TO BE CREATED converted: {summary['to_be_created_converted']}")
    print(f"  Companies needing review: {summary['multiple_matches_phase1'] + summary['multiple_matches_phase2']}")
    print(f"  Remaining without ID: {summary['companies_without_id_after']}")

if __name__ == "__main__":
    main()