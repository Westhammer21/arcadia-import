#!/usr/bin/env python3
"""
Fix missing arc_ columns for records with arc_id populated
Created: 2025-09-03
Purpose: Fill empty arc_ columns by looking up arc_id in Arcadia company database
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

def analyze_missing_columns():
    """Analyze records with arc_id but missing arc_ columns"""
    print("=" * 70)
    print("PHASE 1: ANALYZING MISSING ARC_ COLUMNS")
    print("=" * 70)
    
    # Load the unmapped transactions
    input_file = Path('output/ig_arc_unmapped_FINAL_COMPLETE.csv')
    print(f"\n1. Loading data from: {input_file}")
    
    df = pd.read_csv(input_file, encoding='utf-8')
    total_records = len(df)
    print(f"   Total records: {total_records}")
    
    # Get all arc_ columns
    arc_columns = [col for col in df.columns if col.startswith('arc_') and col != 'arc_id']
    print(f"\n2. Arc_ columns found: {len(arc_columns)}")
    for col in arc_columns[:5]:  # Show first 5
        print(f"   - {col}")
    if len(arc_columns) > 5:
        print(f"   ... and {len(arc_columns) - 5} more")
    
    # Find records with arc_id but empty arc_name (indicator of missing data)
    has_arc_id = df['arc_id'].notna() & (df['arc_id'].astype(str).str.strip() != '') & (df['arc_id'].astype(str) != 'nan')
    missing_arc_name = df['arc_name'].isna() | (df['arc_name'].astype(str).str.strip() == '') | (df['arc_name'].astype(str) == 'nan')
    
    affected_mask = has_arc_id & missing_arc_name
    affected_records = df[affected_mask]
    
    print(f"\n3. Records with arc_id but missing arc_ columns:")
    print(f"   - Total affected: {len(affected_records)}")
    print(f"   - Percentage: {len(affected_records)/total_records*100:.1f}%")
    
    # Get unique arc_ids that need fixing
    unique_ids = affected_records['arc_id'].unique()
    print(f"\n4. Unique arc_ids to fix: {len(unique_ids)}")
    
    # List provided by user
    user_provided_ids = [774, 1166, 1245, 1077, 3408, 774, 1522, 3470, 3340, 3471, 
                         389, 1652, 590, 9344, 3313, 3343, 2015, 916, 531, 3712, 
                         3852, 2229, 2271, 739, 716, 670, 2391, 611, 459, 3472, 
                         2605, 439, 2271, 2791, 9540, 8247, 599, 2356, 3165, 8776]
    
    # Convert to set for comparison
    user_ids_set = set(str(id) for id in user_provided_ids)
    found_ids_set = set(str(int(float(id))) for id in unique_ids if pd.notna(id))
    
    print(f"\n5. Comparison with user-provided list:")
    print(f"   - User provided: {len(set(user_provided_ids))} unique IDs")
    print(f"   - Found in data: {len(found_ids_set)} unique IDs")
    print(f"   - Match: {user_ids_set == found_ids_set}")
    
    # Show any differences
    if user_ids_set != found_ids_set:
        only_in_user = user_ids_set - found_ids_set
        only_in_data = found_ids_set - user_ids_set
        
        if only_in_user:
            print(f"   - IDs in user list but not found: {sorted(only_in_user)}")
        if only_in_data:
            print(f"   - IDs found but not in user list: {sorted(only_in_data)}")
    
    # Sample of affected records
    print(f"\n6. Sample affected records:")
    for idx, row in affected_records.head(5).iterrows():
        print(f"   Row {idx}: arc_id={row['arc_id']}, Target='{row['Target name']}'")
    
    return df, affected_records, affected_mask, arc_columns

def load_arcadia_companies():
    """Load Arcadia company reference data"""
    print("\n" + "=" * 70)
    print("PHASE 2: LOADING ARCADIA COMPANY DATA")
    print("=" * 70)
    
    arcadia_file = Path('src/company-names-arcadia.csv')
    print(f"\n1. Loading Arcadia companies from: {arcadia_file}")
    
    if not arcadia_file.exists():
        print(f"   ERROR: File not found: {arcadia_file}")
        return None
    
    arcadia_df = pd.read_csv(arcadia_file, encoding='utf-8')
    print(f"   Total companies: {len(arcadia_df)}")
    
    # Check if all required columns exist
    print(f"\n2. Arcadia columns available:")
    for col in arcadia_df.columns[:10]:  # Show first 10
        non_null = arcadia_df[col].notna().sum()
        print(f"   - {col}: {non_null} non-null values")
    if len(arcadia_df.columns) > 10:
        print(f"   ... and {len(arcadia_df.columns) - 10} more columns")
    
    return arcadia_df

def create_arcadia_lookup(arcadia_df):
    """Create lookup dictionary from Arcadia data"""
    print("\n" + "=" * 70)
    print("PHASE 3: CREATING LOOKUP DICTIONARY")
    print("=" * 70)
    
    arcadia_lookup = {}
    duplicates = []
    
    for idx, row in arcadia_df.iterrows():
        arc_id = str(int(row['id'])) if pd.notna(row['id']) else None
        
        if arc_id:
            if arc_id in arcadia_lookup:
                duplicates.append(arc_id)
            
            # Store all company data
            arcadia_lookup[arc_id] = {
                'arc_status': row.get('status', ''),
                'arc_name': row.get('name', ''),
                'arc_also_known_as': row.get('also_known_as', ''),
                'arc_aliases': row.get('aliases', ''),
                'arc_type': row.get('type', ''),
                'arc_founded': row.get('founded', ''),
                'arc_hq_country': row.get('hq_country', ''),
                'arc_hq_region': row.get('hq_region', ''),
                'arc_ownership': row.get('ownership', ''),
                'arc_sector': row.get('sector', ''),
                'arc_segment': row.get('segment', ''),
                'arc_features': row.get('features', ''),
                'arc_specialization': row.get('specialization', ''),
                'arc_aum': row.get('aum', ''),
                'arc_parent_company': row.get('parent_company', ''),
                'arc_transactions_count': row.get('transactions_count', ''),
                'arc_was_added': row.get('was_added', ''),
                'arc_created_by': row.get('created_by', ''),
                'arc_was_changed': row.get('was_changed', ''),
                'arc_modified_by': row.get('modified_by', ''),
                'arc_search_index': row.get('search_index', ''),
            }
    
    print(f"\n   Created lookup with {len(arcadia_lookup)} companies")
    if duplicates:
        print(f"   WARNING: Found {len(duplicates)} duplicate IDs: {duplicates[:5]}")
    
    return arcadia_lookup

def fix_missing_columns(df, affected_mask, arcadia_lookup, arc_columns):
    """Fix missing arc_ columns by looking up arc_id"""
    print("\n" + "=" * 70)
    print("PHASE 4: FIXING MISSING COLUMNS")
    print("=" * 70)
    
    fixed_count = 0
    not_found = []
    updates_log = []
    
    # Get indices of affected records
    affected_indices = df.index[affected_mask].tolist()
    print(f"\n   Processing {len(affected_indices)} records...")
    
    for idx in affected_indices:
        arc_id = str(int(float(df.at[idx, 'arc_id']))) if pd.notna(df.at[idx, 'arc_id']) else None
        
        if arc_id and arc_id in arcadia_lookup:
            # Get company data
            company_data = arcadia_lookup[arc_id]
            
            # Update all arc_ columns
            for col_name, value in company_data.items():
                if col_name in df.columns:
                    old_value = df.at[idx, col_name]
                    df.at[idx, col_name] = value if pd.notna(value) else ''
                    
                    # Log the update
                    if col_name == 'arc_name':  # Log only arc_name for brevity
                        updates_log.append({
                            'row': idx,
                            'arc_id': arc_id,
                            'column': col_name,
                            'old_value': old_value,
                            'new_value': value
                        })
            
            fixed_count += 1
        elif arc_id:
            not_found.append(arc_id)
    
    print(f"\n   Results:")
    print(f"   - Records fixed: {fixed_count}")
    print(f"   - Arc_ids not found: {len(not_found)}")
    
    if not_found:
        print(f"\n   Arc_ids not found in Arcadia database:")
        for nf_id in sorted(set(not_found))[:10]:
            print(f"   - {nf_id}")
        if len(set(not_found)) > 10:
            print(f"   ... and {len(set(not_found)) - 10} more")
    
    # Show sample of updates
    if updates_log:
        print(f"\n   Sample updates (first 5):")
        for log in updates_log[:5]:
            print(f"   Row {log['row']}: arc_id={log['arc_id']}, {log['column']}='{log['new_value']}'")
    
    return df, fixed_count, not_found, updates_log

def verify_fixes(df, original_affected_mask):
    """Verify that fixes were applied correctly"""
    print("\n" + "=" * 70)
    print("PHASE 5: VERIFICATION")
    print("=" * 70)
    
    # Check if any records still have arc_id but missing arc_name
    has_arc_id = df['arc_id'].notna() & (df['arc_id'].astype(str).str.strip() != '') & (df['arc_id'].astype(str) != 'nan')
    missing_arc_name = df['arc_name'].isna() | (df['arc_name'].astype(str).str.strip() == '') | (df['arc_name'].astype(str) == 'nan')
    
    still_affected = has_arc_id & missing_arc_name
    still_affected_count = still_affected.sum()
    
    print(f"\n1. Verification Results:")
    print(f"   - Originally affected: {original_affected_mask.sum()}")
    print(f"   - Still affected: {still_affected_count}")
    print(f"   - Fixed: {original_affected_mask.sum() - still_affected_count}")
    print(f"   - Success rate: {(original_affected_mask.sum() - still_affected_count)/original_affected_mask.sum()*100:.1f}%")
    
    # Check for duplicate arc_ids with different data
    arc_id_groups = df[df['arc_id'].notna()].groupby('arc_id')
    inconsistent = []
    
    for arc_id, group in arc_id_groups:
        if len(group) > 1:
            # Check if arc_name is consistent
            unique_names = group['arc_name'].unique()
            if len(unique_names) > 1:
                inconsistent.append(arc_id)
    
    print(f"\n2. Data Consistency:")
    print(f"   - Duplicate arc_ids with inconsistent data: {len(inconsistent)}")
    if inconsistent:
        print(f"   - Inconsistent IDs: {inconsistent[:5]}")
    
    return still_affected_count, inconsistent

def generate_report(fixed_count, not_found, original_affected, still_affected):
    """Generate report of fixes applied"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = []
    report.append("\n#### 7. Arc_ Column Population Fix (2025-09-03)")
    report.append("Fixed missing company metadata for records with arc_id but empty arc_ columns:")
    report.append("")
    report.append("**Issue Identified:**")
    report.append(f"- Records with arc_id but missing metadata: {original_affected}")
    report.append("- Cause: Re-matching script only populated arc_id, not full metadata")
    report.append("")
    report.append("**Fix Applied:**")
    report.append(f"- Records successfully fixed: {fixed_count}")
    report.append(f"- Arc_ids not found in Arcadia: {len(set(not_found)) if not_found else 0}")
    report.append(f"- Remaining unfixed: {still_affected}")
    report.append(f"- Success rate: {(original_affected - still_affected)/original_affected*100:.1f}%")
    report.append("")
    report.append("**Columns Populated:**")
    report.append("- arc_status, arc_name, arc_type")
    report.append("- arc_founded, arc_hq_country, arc_hq_region")
    report.append("- arc_ownership, arc_sector, arc_segment")
    report.append("- Plus 12 additional metadata columns")
    
    return "\n".join(report)

def main():
    """Main execution function"""
    print("\n" + "=" * 80)
    print(" FIX MISSING ARC_ COLUMNS FOR POPULATED ARC_ID VALUES ")
    print("=" * 80)
    
    # Phase 1: Analyze current state
    df, affected_records, affected_mask, arc_columns = analyze_missing_columns()
    original_affected_count = len(affected_records)
    
    if original_affected_count == 0:
        print("\nNo records found with arc_id but missing arc_ columns. Nothing to fix.")
        return
    
    # Phase 2: Load Arcadia companies
    arcadia_df = load_arcadia_companies()
    if arcadia_df is None:
        print("\nFailed to load Arcadia companies. Exiting.")
        return
    
    # Phase 3: Create lookup
    arcadia_lookup = create_arcadia_lookup(arcadia_df)
    
    # Create backup
    print("\nCreating backup...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = Path(f'output/ig_arc_unmapped_BACKUP_{timestamp}.csv')
    df.to_csv(backup_file, index=False, encoding='utf-8')
    print(f"   Backup saved to: {backup_file}")
    
    # Phase 4: Fix missing columns
    df_fixed, fixed_count, not_found, updates_log = fix_missing_columns(df, affected_mask, arcadia_lookup, arc_columns)
    
    # Phase 5: Verify fixes
    still_affected_count, inconsistent = verify_fixes(df_fixed, affected_mask)
    
    # Save updated data
    output_file = Path('output/ig_arc_unmapped_FINAL_COMPLETE.csv')
    df_fixed.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n   Updated data saved to: {output_file}")
    
    # Generate report
    report_text = generate_report(fixed_count, not_found, original_affected_count, still_affected_count)
    
    # Save report to file
    report_file = Path(f'output/ARC_COLUMN_FIX_REPORT_{timestamp}.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"Arc_ Column Fix Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        f.write(report_text)
    
    print(f"\n   Report saved to: {report_file}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"\n✓ Processed {original_affected_count} records with missing arc_ columns")
    print(f"✓ Fixed {fixed_count} records successfully")
    if not_found:
        print(f"⚠ {len(set(not_found))} arc_ids not found in Arcadia database")
    if still_affected_count > 0:
        print(f"⚠ {still_affected_count} records still need attention")
    else:
        print(f"✓ All records with arc_id now have complete metadata")
    
    return report_text

if __name__ == "__main__":
    report = main()