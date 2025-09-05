"""
Match Arcadia IDs for existing companies using CASE-SENSITIVE exact matching
Critical: This script performs case-sensitive matching to ensure 100% accuracy
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import random
from pathlib import Path

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

def load_data():
    """Load both the unmapped companies and Arcadia database"""
    print("[LOAD] Loading data files...")
    
    # Load unmapped companies
    unmapped_df = pd.read_csv('output/arcadia_company_unmapped.csv')
    print(f"  - Loaded {len(unmapped_df)} unmapped companies")
    
    # Load Arcadia database
    arcadia_df = pd.read_csv('src/company-names-arcadia.csv')
    print(f"  - Loaded {len(arcadia_df)} Arcadia companies")
    
    return unmapped_df, arcadia_df

def analyze_data(unmapped_df, arcadia_df):
    """Analyze the data before processing"""
    print("\n[ANALYSIS] Data Overview:")
    print(f"  Unmapped companies by status:")
    status_counts = unmapped_df['status'].value_counts()
    for status, count in status_counts.items():
        print(f"    - {status}: {count}")
    
    # Companies needing ID matching
    need_matching = unmapped_df[unmapped_df['status'] != 'TO BE CREATED']
    print(f"\n  Companies needing ID match: {len(need_matching)}")
    
    # Check for existing IDs
    existing_ids = need_matching[need_matching['id'].notna()]
    print(f"  Companies with existing IDs: {len(existing_ids)}")
    if len(existing_ids) > 0:
        print(f"    Example: {existing_ids.iloc[0]['name']} (ID: {existing_ids.iloc[0]['id']})")
    
    # Arcadia database stats
    print(f"\n  Arcadia database stats:")
    print(f"    - Total companies: {len(arcadia_df)}")
    print(f"    - With also_known_as: {arcadia_df['also_known_as'].notna().sum()}")
    print(f"    - With aliases: {arcadia_df['aliases'].notna().sum()}")
    
    return need_matching

def build_matching_indexes(arcadia_df):
    """Build case-sensitive lookup dictionaries"""
    print("\n[BUILD] Creating case-sensitive matching indexes...")
    
    name_to_id = {}
    aka_to_id = {}
    alias_to_id = {}
    
    conflicts = []
    
    for _, row in arcadia_df.iterrows():
        arc_id = row['id']
        
        # Index by name (case-sensitive)
        if pd.notna(row['name']) and row['name'] != '':
            name = str(row['name'])
            if name in name_to_id:
                conflicts.append(f"Duplicate name: '{name}' (IDs: {name_to_id[name]}, {arc_id})")
            name_to_id[name] = arc_id
        
        # Index by also_known_as (case-sensitive)
        if pd.notna(row['also_known_as']) and row['also_known_as'] != '':
            aka = str(row['also_known_as'])
            if aka in aka_to_id:
                conflicts.append(f"Duplicate aka: '{aka}' (IDs: {aka_to_id[aka]}, {arc_id})")
            aka_to_id[aka] = arc_id
        
        # Index by aliases (comma-separated, case-sensitive)
        if pd.notna(row['aliases']) and row['aliases'] != '':
            aliases = str(row['aliases']).split(',')
            for alias in aliases:
                alias = alias.strip()
                if alias:
                    if alias in alias_to_id:
                        conflicts.append(f"Duplicate alias: '{alias}' (IDs: {alias_to_id[alias]}, {arc_id})")
                    alias_to_id[alias] = arc_id
    
    print(f"  - Name index: {len(name_to_id)} entries")
    print(f"  - Also known as index: {len(aka_to_id)} entries")
    print(f"  - Aliases index: {len(alias_to_id)} entries")
    
    if conflicts:
        print(f"\n  [WARNING] Found {len(conflicts)} conflicts:")
        for conflict in conflicts[:5]:
            print(f"    - {conflict}")
    
    return name_to_id, aka_to_id, alias_to_id

def match_company(row, name_to_id, aka_to_id, alias_to_id):
    """Match a single company using case-sensitive exact matching"""
    # Skip if TO BE CREATED
    if row['status'] == 'TO BE CREATED':
        return None, None
    
    # Skip if already has ID
    if pd.notna(row['id']) and row['id'] != '':
        return row['id'], 'existing'
    
    company_name = str(row['name']) if pd.notna(row['name']) else ''
    
    # Try exact name match (case-sensitive)
    if company_name in name_to_id:
        return name_to_id[company_name], 'name_match'
    
    # Try also_known_as match
    if company_name in aka_to_id:
        return aka_to_id[company_name], 'aka_match'
    
    # Try aliases match
    if company_name in alias_to_id:
        return alias_to_id[company_name], 'alias_match'
    
    return None, None

def perform_matching(unmapped_df, name_to_id, aka_to_id, alias_to_id):
    """Perform matching for all companies"""
    print("\n[MATCH] Performing case-sensitive ID matching...")
    
    match_log = []
    statistics = {
        'total_processed': 0,
        'name_match': 0,
        'aka_match': 0,
        'alias_match': 0,
        'existing': 0,
        'no_match': 0,
        'to_be_created': 0
    }
    
    for idx, row in unmapped_df.iterrows():
        if row['status'] == 'TO BE CREATED':
            statistics['to_be_created'] += 1
            continue
        
        statistics['total_processed'] += 1
        
        matched_id, match_type = match_company(row, name_to_id, aka_to_id, alias_to_id)
        
        if matched_id:
            unmapped_df.at[idx, 'id'] = matched_id
            statistics[match_type] = statistics.get(match_type, 0) + 1
            
            match_log.append({
                'company_name': row['name'],
                'status': row['status'],
                'matched_id': matched_id,
                'match_type': match_type
            })
        else:
            statistics['no_match'] += 1
            match_log.append({
                'company_name': row['name'],
                'status': row['status'],
                'matched_id': None,
                'match_type': 'no_match'
            })
    
    print(f"  Matching Results:")
    print(f"    - Total processed: {statistics['total_processed']}")
    print(f"    - Name matches: {statistics['name_match']}")
    print(f"    - Also known as matches: {statistics['aka_match']}")
    print(f"    - Alias matches: {statistics['alias_match']}")
    print(f"    - Already had ID: {statistics['existing']}")
    print(f"    - No match found: {statistics['no_match']}")
    print(f"    - TO BE CREATED (skipped): {statistics['to_be_created']}")
    
    return unmapped_df, match_log, statistics

def perform_validation(unmapped_df, arcadia_df, match_log, sample_size=50):
    """Perform random validation checks"""
    print("\n[VALIDATE] Performing 50 random validation checks...")
    
    # Filter match_log for companies that were processed
    processed_log = [m for m in match_log if m['status'] != 'TO BE CREATED']
    
    # Stratified sampling
    matched_companies = [m for m in processed_log if m['matched_id'] is not None]
    unmatched_companies = [m for m in processed_log if m['matched_id'] is None]
    
    # Calculate sample sizes
    n_matched_sample = min(30, len(matched_companies))
    n_unmatched_sample = min(20, len(unmatched_companies))
    
    validation_sample = []
    
    # Sample matched companies
    if matched_companies:
        matched_sample = random.sample(matched_companies, n_matched_sample)
        validation_sample.extend(matched_sample)
    
    # Sample unmatched companies
    if unmatched_companies:
        unmatched_sample = random.sample(unmatched_companies, n_unmatched_sample)
        validation_sample.extend(unmatched_sample)
    
    print(f"  Validation sample: {len(validation_sample)} companies")
    print(f"    - Matched: {n_matched_sample}")
    print(f"    - Unmatched: {n_unmatched_sample}")
    
    # Perform validation
    validation_results = []
    errors_found = 0
    
    for item in validation_sample:
        company_name = item['company_name']
        matched_id = item['matched_id']
        match_type = item['match_type']
        
        # Verify the match
        is_correct = False
        expected_match = None
        
        if matched_id:
            # Check if the match is correct
            arc_company = arcadia_df[arcadia_df['id'] == matched_id]
            if not arc_company.empty:
                arc_row = arc_company.iloc[0]
                
                # Check case-sensitive exact match
                if match_type == 'name_match':
                    is_correct = (arc_row['name'] == company_name)
                    expected_match = arc_row['name']
                elif match_type == 'aka_match':
                    is_correct = (arc_row['also_known_as'] == company_name)
                    expected_match = arc_row['also_known_as']
                elif match_type == 'alias_match':
                    if pd.notna(arc_row['aliases']):
                        aliases = [a.strip() for a in str(arc_row['aliases']).split(',')]
                        is_correct = company_name in aliases
                        expected_match = arc_row['aliases']
        else:
            # Verify no match exists
            no_name_match = company_name not in arcadia_df['name'].values
            no_aka_match = True
            no_alias_match = True
            
            if arcadia_df['also_known_as'].notna().any():
                no_aka_match = company_name not in arcadia_df['also_known_as'].values
            
            # Check aliases
            for aliases in arcadia_df['aliases'].dropna():
                alias_list = [a.strip() for a in str(aliases).split(',')]
                if company_name in alias_list:
                    no_alias_match = False
                    break
            
            is_correct = no_name_match and no_aka_match and no_alias_match
            
            if not is_correct:
                # Find what was missed
                if not no_name_match:
                    expected_match = "Should have matched on name"
                elif not no_aka_match:
                    expected_match = "Should have matched on also_known_as"
                elif not no_alias_match:
                    expected_match = "Should have matched on alias"
        
        if not is_correct:
            errors_found += 1
        
        validation_results.append({
            'company_name': company_name,
            'matched_id': matched_id,
            'match_type': match_type,
            'is_correct': is_correct,
            'expected': expected_match
        })
    
    # Print validation summary
    print(f"\n  Validation Results:")
    print(f"    - Total checked: {len(validation_results)}")
    print(f"    - Correct: {len(validation_results) - errors_found}")
    print(f"    - Errors: {errors_found}")
    print(f"    - Accuracy: {((len(validation_results) - errors_found) / len(validation_results) * 100):.1f}%")
    
    if errors_found > 0:
        print("\n  [ERROR] Validation errors found:")
        for result in validation_results:
            if not result['is_correct']:
                print(f"    - {result['company_name']}: {result['expected']}")
    
    return validation_results

def save_results(unmapped_df, match_log, statistics, validation_results):
    """Save all results and generate reports"""
    print("\n[SAVE] Saving results...")
    
    # Save updated unmapped file
    output_file = 'output/arcadia_company_unmapped.csv'
    unmapped_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"  - Updated file saved: {output_file}")
    
    # Save match log
    match_log_df = pd.DataFrame(match_log)
    match_log_file = 'output/arcadia_id_match_log.csv'
    match_log_df.to_csv(match_log_file, index=False, encoding='utf-8')
    print(f"  - Match log saved: {match_log_file}")
    
    # Save validation results
    validation_df = pd.DataFrame(validation_results)
    validation_file = 'output/arcadia_id_validation_results.csv'
    validation_df.to_csv(validation_file, index=False, encoding='utf-8')
    print(f"  - Validation results saved: {validation_file}")
    
    # Generate summary report
    report = f"""# Arcadia ID Matching Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Total Companies**: {len(unmapped_df)}
- **Companies Processed**: {statistics['total_processed']}
- **Successful Matches**: {statistics['name_match'] + statistics['aka_match'] + statistics['alias_match'] + statistics['existing']}
- **No Match Found**: {statistics['no_match']}
- **Match Rate**: {((statistics['name_match'] + statistics['aka_match'] + statistics['alias_match']) / max(1, statistics['total_processed'] - statistics['existing']) * 100):.1f}%

## Match Types
- **Name Matches**: {statistics['name_match']}
- **Also Known As Matches**: {statistics['aka_match']}
- **Alias Matches**: {statistics['alias_match']}
- **Already Had ID**: {statistics['existing']}

## Validation
- **Sample Size**: {len(validation_results)}
- **Validation Accuracy**: {(sum(1 for v in validation_results if v['is_correct']) / len(validation_results) * 100):.1f}%

## Files Generated
- Updated companies: `output/arcadia_company_unmapped.csv`
- Match log: `output/arcadia_id_match_log.csv`
- Validation results: `output/arcadia_id_validation_results.csv`

## Unmatched Companies
Companies with status != 'TO BE CREATED' but no match found: {statistics['no_match']}
See match log for details.
"""
    
    report_file = 'docs/arcadia_id_matching_report.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"  - Report saved: {report_file}")
    
    # Print unmatched companies for review
    unmatched = [m for m in match_log if m['match_type'] == 'no_match']
    if unmatched:
        print(f"\n[REVIEW] {len(unmatched)} companies need manual review (no match found):")
        for i, company in enumerate(unmatched[:10], 1):
            print(f"  {i}. {company['company_name']} (Status: {company['status']})")
        if len(unmatched) > 10:
            print(f"  ... and {len(unmatched) - 10} more")

def main():
    print("[START] Arcadia ID Matching Process (CASE-SENSITIVE)")
    print("=" * 60)
    
    # Load data
    unmapped_df, arcadia_df = load_data()
    
    # Analyze data
    need_matching = analyze_data(unmapped_df, arcadia_df)
    
    # Build indexes
    name_to_id, aka_to_id, alias_to_id = build_matching_indexes(arcadia_df)
    
    # Perform matching
    unmapped_df, match_log, statistics = perform_matching(
        unmapped_df, name_to_id, aka_to_id, alias_to_id
    )
    
    # Validate results
    validation_results = perform_validation(
        unmapped_df, arcadia_df, match_log, sample_size=50
    )
    
    # Save everything
    save_results(unmapped_df, match_log, statistics, validation_results)
    
    print("\n" + "=" * 60)
    print("[SUCCESS] ID matching complete!")
    print(f"Match rate: {((statistics['name_match'] + statistics['aka_match'] + statistics['alias_match']) / max(1, statistics['total_processed'] - statistics['existing']) * 100):.1f}%")
    print(f"Validation accuracy: {(sum(1 for v in validation_results if v['is_correct']) / len(validation_results) * 100):.1f}%")

if __name__ == "__main__":
    main()