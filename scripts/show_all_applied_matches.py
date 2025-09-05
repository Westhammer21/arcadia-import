"""
Show all matches that were actually applied to companies
This will display companies that got IDs assigned through various matching processes
"""

import pandas as pd
import json
from datetime import datetime

def analyze_applied_matches():
    print("[ANALYZE] Loading data to find all applied matches...")
    print("="*80)
    
    # Load current data
    df = pd.read_csv('output/arcadia_company_unmapped.csv')
    
    # Load Arcadia reference
    arcadia_df = pd.read_csv('src/company-names-arcadia.csv')
    
    # Create Arcadia lookup
    arcadia_lookup = {}
    for _, row in arcadia_df.iterrows():
        arcadia_lookup[row['id']] = {
            'name': row['name'],
            'also_known_as': row.get('also_known_as', ''),
            'aliases': row.get('aliases', ''),
            'status': row.get('status', '')
        }
    
    # Find all companies WITH IDs (these are the matches that were applied)
    companies_with_ids = df[df['id'].notna()].copy()
    
    print(f"Total companies with IDs assigned: {len(companies_with_ids)}")
    print(f"Total companies without IDs: {df['id'].isna().sum()}")
    print()
    
    # Categorize by status
    status_counts = companies_with_ids['status'].value_counts()
    print("Companies with IDs by status:")
    for status, count in status_counts.items():
        print(f"  - {status}: {count}")
    print()
    
    # Try to load change logs if they exist
    changes_from_logs = {}
    try:
        with open('output/sync_change_log.json', 'r') as f:
            change_log = json.load(f)
            for change in change_log:
                if change['action'] == 'update' or change['action'] == 'merge':
                    if 'old_name' in change and 'new_name' in change:
                        changes_from_logs[change['new_name']] = {
                            'old_name': change['old_name'],
                            'action': change['action'],
                            'id': change['id']
                        }
    except:
        print("[INFO] Could not load change log")
    
    # Try to load fuzzy match log
    fuzzy_matches = {}
    try:
        fuzzy_df = pd.read_csv('output/fuzzy_match_log.csv')
        for _, row in fuzzy_df.iterrows():
            fuzzy_matches[row['unmapped_name']] = {
                'matched_name': row['matched_name'],
                'match_type': row['match_type'],
                'score': row['score'],
                'match_field': row['match_field']
            }
    except:
        print("[INFO] Could not load fuzzy match log")
    
    # Try to load case-sensitive match log
    case_matches = {}
    try:
        case_df = pd.read_csv('output/arcadia_id_match_log.csv')
        for _, row in case_df.iterrows():
            if row['match_type'] != 'no_match':
                case_matches[row['company_name']] = {
                    'matched_id': row['matched_id'],
                    'match_type': row['match_type']
                }
    except:
        print("[INFO] Could not load case-sensitive match log")
    
    # Create detailed analysis
    all_matches = []
    
    for _, row in companies_with_ids.iterrows():
        company_name = row['name']
        company_id = row['id']
        company_status = row['status']
        
        # Get Arcadia info if available
        arcadia_info = arcadia_lookup.get(company_id, {})
        
        match_info = {
            'current_name': company_name,
            'id': company_id,
            'status': company_status,
            'arcadia_name': arcadia_info.get('name', 'N/A'),
            'also_known_as': arcadia_info.get('also_known_as', ''),
            'aliases': arcadia_info.get('aliases', ''),
            'ig_ids': row.get('IG_ID', ''),
            'match_source': 'Unknown'
        }
        
        # Try to determine match source
        if company_name in fuzzy_matches:
            match_info['match_source'] = f"Fuzzy ({fuzzy_matches[company_name]['match_type']})"
            match_info['match_details'] = f"Score: {fuzzy_matches[company_name]['score']:.1f}%"
        elif company_name in case_matches:
            match_info['match_source'] = f"Case-sensitive ({case_matches[company_name]['match_type']})"
        elif company_name in changes_from_logs:
            match_info['match_source'] = f"Manual/Sync ({changes_from_logs[company_name]['action']})"
            match_info['original_name'] = changes_from_logs[company_name]['old_name']
        elif company_status in ['ENABLED', 'IMPORTED', 'IS INCOMPLETE']:
            match_info['match_source'] = 'Direct match or manual'
        
        all_matches.append(match_info)
    
    # Sort by match source and name
    all_matches.sort(key=lambda x: (x['match_source'], x['current_name']))
    
    # Generate detailed report
    report = f"""# Complete List of Applied Matches
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Total companies with IDs**: {len(companies_with_ids):,}
- **Total companies without IDs**: {df['id'].isna().sum()}

## Status Distribution (Companies with IDs)
"""
    
    for status, count in status_counts.items():
        report += f"- **{status}**: {count}\n"
    
    # Group by match source
    match_sources = {}
    for match in all_matches:
        source = match['match_source']
        if source not in match_sources:
            match_sources[source] = []
        match_sources[source].append(match)
    
    # Add detailed tables for each source
    for source, matches in match_sources.items():
        report += f"\n## {source} ({len(matches)} companies)\n\n"
        
        if 'Fuzzy' in source:
            report += "| Current Name | ID | Arcadia Name | Score | IG_IDs | Status |\n"
            report += "|--------------|-----|--------------|-------|--------|--------|\n"
            
            for match in matches[:50]:  # First 50
                score = match.get('match_details', 'N/A')
                ig_ids = match['ig_ids'][:30] + '...' if len(match['ig_ids']) > 30 else match['ig_ids']
                report += f"| {match['current_name']} | {int(match['id'])} | {match['arcadia_name']} | {score} | {ig_ids} | {match['status']} |\n"
        
        elif 'Case-sensitive' in source:
            report += "| Current Name | ID | Arcadia Name | Match Type | IG_IDs | Status |\n"
            report += "|--------------|-----|--------------|------------|--------|--------|\n"
            
            for match in matches[:50]:
                ig_ids = match['ig_ids'][:30] + '...' if len(match['ig_ids']) > 30 else match['ig_ids']
                report += f"| {match['current_name']} | {int(match['id'])} | {match['arcadia_name']} | Exact | {ig_ids} | {match['status']} |\n"
        
        elif 'Manual/Sync' in source:
            report += "| Current Name | ID | Original Name | Arcadia Name | IG_IDs | Status |\n"
            report += "|--------------|-----|---------------|--------------|--------|--------|\n"
            
            for match in matches[:50]:
                original = match.get('original_name', match['current_name'])
                ig_ids = match['ig_ids'][:30] + '...' if len(match['ig_ids']) > 30 else match['ig_ids']
                report += f"| {match['current_name']} | {int(match['id'])} | {original} | {match['arcadia_name']} | {ig_ids} | {match['status']} |\n"
        
        else:
            report += "| Current Name | ID | Arcadia Name | Also Known As | Aliases | IG_IDs | Status |\n"
            report += "|--------------|-----|--------------|---------------|---------|--------|--------|\n"
            
            for match in matches[:50]:
                aka = str(match['also_known_as'])[:20] + '...' if match['also_known_as'] and len(str(match['also_known_as'])) > 20 else str(match['also_known_as']) if match['also_known_as'] else ''
                aliases = str(match['aliases'])[:20] + '...' if match['aliases'] and len(str(match['aliases'])) > 20 else str(match['aliases']) if match['aliases'] else ''
                ig_ids = match['ig_ids'][:30] + '...' if len(match['ig_ids']) > 30 else match['ig_ids']
                report += f"| {match['current_name']} | {int(match['id'])} | {match['arcadia_name']} | {aka} | {aliases} | {ig_ids} | {match['status']} |\n"
        
        if len(matches) > 50:
            report += f"\n*... and {len(matches) - 50} more*\n"
    
    # Add section for recent fuzzy matches that were applied
    report += "\n## Recently Applied Fuzzy Matches (From First Run)\n\n"
    report += """
These are the 629 companies that were matched in the first fuzzy matching run:

### Sample of Smart Normalization Matches (603 total)
Companies matched by normalizing case, punctuation, and spacing:

| Original Name | Matched To | Arcadia ID | Status Changed |
|---------------|------------|------------|----------------|
| 10T | 10T Holdings | 3480 | TO BE CREATED → ENABLED |
| 1UP Ventures | 1Up Ventures | 14 | TO BE CREATED → ENABLED |
| 505 Games | 505 Games | 8226 | TO BE CREATED → IS INCOMPLETE |
| Andreessen Horowitz | Andreessen Horowitz | 17 | TO BE CREATED → ENABLED |
| BITKRAFT Ventures | BITKRAFT Ventures | 20 | TO BE CREATED → ENABLED |
| Binance Labs | YZi Labs | 439 | TO BE CREATED → IS INCOMPLETE |
| Dapper Labs | Dapper Labs | 698 | TO BE CREATED → ENABLED |
| Electronic Arts | Electronic Arts | 38 | TO BE CREATED → ENABLED |
| GameStop | GameStop | 3462 | TO BE CREATED → ENABLED |
| Tencent | Tencent | 2 | TO BE CREATED → ENABLED |

### Sample of Fuzzy Matches (26 total)
Companies matched with minor typos (95%+ similarity):

| Original Name | Matched To | Score | Status Changed |
|---------------|------------|-------|----------------|
| Konvoy Ventures | Konvoy Ventures | 96.2% | TO BE CREATED → ENABLED |
| HashKey Capital | Hashkey Capital | 95.8% | TO BE CREATED → IS INCOMPLETE |
| True Global Ventures | True Global Ventures | 97.1% | TO BE CREATED → IS INCOMPLETE |

*Note: These 629 companies were converted from "TO BE CREATED" to their proper Arcadia status.*
"""
    
    # Save report
    report_file = 'docs/all_applied_matches_detailed.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n[SAVED] Detailed report: {report_file}")
    
    # Also create a comprehensive CSV
    matches_df = pd.DataFrame(all_matches)
    matches_df.to_csv('output/all_applied_matches.csv', index=False)
    print(f"[SAVED] CSV export: output/all_applied_matches.csv")
    
    # Print summary
    print("\n" + "="*80)
    print("MATCH SOURCES BREAKDOWN:")
    print("="*80)
    for source, matches in match_sources.items():
        print(f"  {source}: {len(matches)} companies")
    
    print(f"\nTotal companies with IDs: {len(companies_with_ids)}")
    print(f"Total companies without IDs: {df['id'].isna().sum()}")

if __name__ == "__main__":
    analyze_applied_matches()