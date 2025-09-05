"""
Merge Dual-Role Companies Script
Merges company cards using smart name matching with 97.5% threshold
Consolidates all IG_IDs and roles for companies with same/similar names
"""

import pandas as pd
import numpy as np
from datetime import datetime
from difflib import SequenceMatcher
import warnings
warnings.filterwarnings('ignore')

def normalize_name(name):
    """Normalize company name for comparison"""
    if pd.isna(name) or name == '':
        return ''
    # Convert to lowercase and strip whitespace
    normalized = str(name).lower().strip()
    # Remove common suffixes and words that don't affect company identity
    for suffix in [' inc.', ' inc', ' ltd.', ' ltd', ' llc', ' corp.', ' corp', 
                   ' limited', ' company', ' co.', ' co', ' plc', ' gmbh', ' ag']:
        normalized = normalized.replace(suffix, '')
    return normalized.strip()

def calculate_similarity(name1, name2):
    """Calculate similarity between two names"""
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)
    
    if norm1 == '' or norm2 == '':
        return 0.0
    
    # Use SequenceMatcher for fuzzy matching
    return SequenceMatcher(None, norm1, norm2).ratio()

def should_merge_names(name1, name2, threshold=0.975):
    """Determine if two names should be merged based on similarity"""
    # Exact match (case-insensitive)
    if normalize_name(name1) == normalize_name(name2):
        return True
    
    # Fuzzy match with high threshold
    similarity = calculate_similarity(name1, name2)
    return similarity >= threshold

def get_metadata_priority(row):
    """Calculate priority score for metadata selection"""
    status = str(row.get('status', '')).upper()
    if 'ENABLED' in status:
        return 3
    elif 'IMPORTED' in status:
        return 2
    elif 'TO BE ENRICHED' in status or 'TO BE CREATED' in status:
        return 1
    return 0

def merge_company_records(group_df):
    """Merge multiple records of the same company into one"""
    if len(group_df) == 0:
        return None
    
    # Sort by metadata priority
    group_df['priority'] = group_df.apply(get_metadata_priority, axis=1)
    group_df = group_df.sort_values('priority', ascending=False)
    
    # Start with the highest priority record
    merged = group_df.iloc[0].to_dict()
    
    # Concatenate IG_IDs and roles
    all_ig_ids = []
    all_roles = []
    
    for _, row in group_df.iterrows():
        ig_ids = str(row.get('IG_ID', '')).split(', ') if pd.notna(row.get('IG_ID')) else []
        roles = str(row.get('investor_role', '')).split(', ') if pd.notna(row.get('investor_role')) else []
        
        all_ig_ids.extend([id for id in ig_ids if id and id != 'nan'])
        all_roles.extend([role for role in roles if role and role != 'nan'])
    
    # Set concatenated values
    merged['IG_ID'] = ', '.join(all_ig_ids) if all_ig_ids else ''
    merged['ig_role'] = ', '.join(all_roles) if all_roles else ''  # Renamed column
    
    # Fill empty fields from other records
    for col in group_df.columns:
        if col not in ['IG_ID', 'investor_role', 'ig_role', 'priority']:
            if pd.isna(merged[col]) or str(merged[col]).strip() == '':
                # Find first non-empty value in this column
                for _, row in group_df.iterrows():
                    val = row[col]
                    if pd.notna(val) and str(val).strip() != '':
                        merged[col] = val
                        break
    
    # Apply transformations
    if 'status' in merged:
        if str(merged['status']).upper() == 'TO BE ENRICHED':
            merged['status'] = 'TO BE CREATED'
    
    if 'ig_role' in merged:
        merged['ig_role'] = merged['ig_role'].lower()
    
    # Remove old column and priority
    if 'investor_role' in merged:
        del merged['investor_role']
    if 'priority' in merged:
        del merged['priority']
    
    return merged

def analyze_ig_conflicts(df):
    """Analyze if any IG_ID appears as both target and investor"""
    conflicts = []
    
    for _, row in df.iterrows():
        ig_ids = str(row.get('IG_ID', '')).split(', ') if pd.notna(row.get('IG_ID')) else []
        roles = str(row.get('investor_role', '')).split(', ') if pd.notna(row.get('investor_role')) else []
        
        if len(ig_ids) != len(roles):
            continue
        
        for i, ig_id in enumerate(ig_ids):
            if ig_id and ig_id != 'nan':
                # Check if this IG_ID appears with different roles
                ig_roles = {}
                for j, check_id in enumerate(ig_ids):
                    if check_id == ig_id and j < len(roles):
                        role = roles[j].lower()
                        if role in ['target', 'TARGET']:
                            role = 'target'
                        if role not in ig_roles:
                            ig_roles[role] = 0
                        ig_roles[role] += 1
                
                if 'target' in ig_roles and len(ig_roles) > 1:
                    conflicts.append({
                        'company': row.get('name', 'Unknown'),
                        'IG_ID': ig_id,
                        'roles': list(ig_roles.keys())
                    })
    
    return conflicts

def main():
    print("[START] Loading company cards data...")
    df = pd.read_csv('output/arcadia_company_cards_deduplicated.csv')
    print(f"[INFO] Loaded {len(df)} company cards")
    
    # Analyze for IG_ID conflicts
    print("\n[ANALYSIS] Checking for IG_IDs appearing as both target and investor...")
    conflicts = analyze_ig_conflicts(df)
    
    if conflicts:
        print(f"[WARNING] Found {len(conflicts)} potential conflicts:")
        for conflict in conflicts[:10]:  # Show first 10
            print(f"  - Company: {conflict['company']}, IG_ID: {conflict['IG_ID']}, Roles: {conflict['roles']}")
    else:
        print("[OK] No IG_IDs found appearing as both target and investor in same transaction")
    
    # Group companies by similar names
    print("\n[PROCESS] Grouping companies by similar names (97.5% threshold)...")
    processed = set()
    company_groups = []
    
    for i, row in df.iterrows():
        if i in processed:
            continue
        
        name = row['name']
        if pd.isna(name):
            continue
        
        # Find all similar companies
        similar_indices = [i]
        for j, other_row in df.iterrows():
            if j <= i or j in processed:
                continue
            
            other_name = other_row['name']
            if pd.notna(other_name) and should_merge_names(name, other_name):
                similar_indices.append(j)
                processed.add(j)
        
        if len(similar_indices) > 1:
            company_groups.append(similar_indices)
            print(f"  [MERGE] Found {len(similar_indices)} records for: {name}")
        else:
            company_groups.append([i])
    
    print(f"[INFO] Identified {len(company_groups)} unique companies (after merging)")
    
    # Merge groups
    print("\n[MERGE] Merging company records...")
    merged_records = []
    duplicate_count = 0
    
    for group_indices in company_groups:
        group_df = df.iloc[group_indices]
        
        if len(group_indices) > 1:
            duplicate_count += len(group_indices) - 1
            
        merged = merge_company_records(group_df)
        if merged:
            merged_records.append(merged)
    
    print(f"[INFO] Merged {duplicate_count} duplicate records")
    
    # Create final dataframe
    final_df = pd.DataFrame(merged_records)
    
    # Ensure column order (remove investor_role, add ig_role)
    columns = [col for col in df.columns if col != 'investor_role']
    if 'ig_role' not in columns:
        columns.append('ig_role')
    
    # Reorder to match original structure
    ordered_cols = []
    for col in columns:
        if col in final_df.columns:
            ordered_cols.append(col)
    
    final_df = final_df[ordered_cols]
    
    # Final validation
    print("\n[VALIDATION] Final data validation:")
    print(f"  - Total companies: {len(final_df)}")
    print(f"  - Reduction from original: {len(df) - len(final_df)} records merged")
    
    # Check for any remaining duplicates
    name_counts = final_df['name'].value_counts()
    duplicates = name_counts[name_counts > 1]
    if len(duplicates) > 0:
        print(f"[WARNING] Found {len(duplicates)} potential remaining duplicates:")
        for name, count in duplicates.head(5).items():
            print(f"    - {name}: {count} records")
    else:
        print("[OK] No duplicate company names remaining")
    
    # Count multi-IG companies
    multi_ig = 0
    max_igs = 0
    for _, row in final_df.iterrows():
        ig_ids = str(row.get('IG_ID', '')).split(', ') if pd.notna(row.get('IG_ID')) else []
        if len(ig_ids) > 1:
            multi_ig += 1
        max_igs = max(max_igs, len(ig_ids))
    
    print(f"  - Companies with multiple IGs: {multi_ig}")
    print(f"  - Maximum IGs per company: {max_igs}")
    
    # Save output
    output_file = 'output/arcadia_company_cards_merged.csv'
    final_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n[SUCCESS] Merged company cards saved to: {output_file}")
    
    # Generate report
    report = f"""# Company Cards Merge Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Original Cards**: {len(df):,}
- **Merged Cards**: {len(final_df):,}
- **Records Merged**: {duplicate_count:,}
- **Reduction**: {round((1 - len(final_df)/len(df)) * 100, 1)}%

## Merge Statistics
- **Companies with Multiple IGs**: {multi_ig:,}
- **Maximum IGs per Company**: {max_igs}
- **Similarity Threshold**: 97.5%

## Transformations Applied
1. Status: "TO BE ENRICHED" -> "TO BE CREATED"
2. Role: "TARGET" -> "target", all roles lowercase
3. Column: "investor_role" -> "ig_role"

## Validation Results
- **IG_ID Conflicts**: {'None detected' if not conflicts else f'{len(conflicts)} found'}
- **Remaining Duplicates**: {'None' if len(duplicates) == 0 else f'{len(duplicates)} potential cases'}

## Output
- **File**: {output_file}
- **Encoding**: UTF-8
- **Ready for Import**: Yes
"""
    
    report_file = 'docs/company_cards_merge_report.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"[REPORT] Merge report saved to: {report_file}")

if __name__ == "__main__":
    main()