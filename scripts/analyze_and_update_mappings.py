#!/usr/bin/env python3
"""
Analyze ARCADIA_TR_ID Changes and Update ARC Columns
=====================================================
1. Compare ARCADIA_TR_ID between old and new versions
2. Create comprehensive change report
3. Update all ARC_* columns from arcadia_database

Author: AI Analytics Team
Date: 2025-09-03
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

def load_csv_safely(file_path, description=""):
    """Load CSV with proper error handling and delimiter detection."""
    print(f"\nLoading {description}: {file_path.name}")
    
    # Try comma-separated first
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        print(f"  [OK] Loaded {len(df)} rows, {len(df.columns)} columns (comma-separated)")
        return df
    except:
        # Try tab-separated
        try:
            df = pd.read_csv(file_path, encoding='utf-8', sep='\t')
            print(f"  [OK] Loaded {len(df)} rows, {len(df.columns)} columns (tab-separated)")
            return df
        except Exception as e:
            print(f"  [ERROR] Failed to load: {e}")
            raise

def compare_arcadia_ids(df_old, df_new):
    """Compare ARCADIA_TR_ID values between old and new versions."""
    print("\n" + "="*60)
    print("COMPARING ARCADIA_TR_ID VALUES")
    print("="*60)
    
    # Ensure IG_ID is numeric for consistent comparison
    df_old['IG_ID'] = pd.to_numeric(df_old['IG_ID'], errors='coerce')
    df_new['IG_ID'] = pd.to_numeric(df_new['IG_ID'], errors='coerce')
    
    # Convert ARCADIA_TR_ID to string, handling NaN values
    df_old['ARCADIA_TR_ID_str'] = df_old['ARCADIA_TR_ID'].fillna('').astype(str)
    df_new['ARCADIA_TR_ID_str'] = df_new['ARCADIA_TR_ID'].fillna('').astype(str)
    
    # Merge on IG_ID to compare
    comparison = pd.merge(
        df_old[['IG_ID', 'Target name', 'ARCADIA_TR_ID_str']],
        df_new[['IG_ID', 'ARCADIA_TR_ID_str']],
        on='IG_ID',
        suffixes=('_old', '_new'),
        how='outer'
    )
    
    # Identify changes
    changes = []
    
    for idx, row in comparison.iterrows():
        ig_id = row['IG_ID']
        old_id = row.get('ARCADIA_TR_ID_str_old', '')
        new_id = row.get('ARCADIA_TR_ID_str_new', '')
        target = row.get('Target name', '')
        
        # Skip if IG_ID is NaN
        if pd.isna(ig_id):
            continue
            
        # Convert empty strings back to representation
        old_id = old_id if old_id != '' and old_id != 'nan' else 'EMPTY'
        new_id = new_id if new_id != '' and new_id != 'nan' else 'EMPTY'
        
        # Determine change type
        if old_id == 'EMPTY' and new_id != 'EMPTY':
            change_type = 'NEW_MAPPING'
            changes.append({
                'IG_ID': int(ig_id),
                'Target Name': target,
                'Change Type': change_type,
                'Old ARCADIA_TR_ID': '',
                'New ARCADIA_TR_ID': new_id,
                'Status': 'Added'
            })
        elif old_id != 'EMPTY' and new_id == 'EMPTY':
            change_type = 'REMOVED_MAPPING'
            changes.append({
                'IG_ID': int(ig_id),
                'Target Name': target,
                'Change Type': change_type,
                'Old ARCADIA_TR_ID': old_id,
                'New ARCADIA_TR_ID': '',
                'Status': 'Removed'
            })
        elif old_id != new_id and old_id != 'EMPTY' and new_id != 'EMPTY':
            change_type = 'MODIFIED_ID'
            changes.append({
                'IG_ID': int(ig_id),
                'Target Name': target,
                'Change Type': change_type,
                'Old ARCADIA_TR_ID': old_id,
                'New ARCADIA_TR_ID': new_id,
                'Status': 'Modified'
            })
    
    changes_df = pd.DataFrame(changes)
    
    # Sort by IG_ID
    if not changes_df.empty:
        changes_df = changes_df.sort_values('IG_ID')
    
    # Print summary
    print(f"\nTotal records analyzed: {len(comparison)}")
    print(f"Records with changes: {len(changes_df)}")
    
    if not changes_df.empty:
        print(f"\nBreakdown by change type:")
        print(changes_df['Change Type'].value_counts().to_string())
    
    return changes_df

def create_change_report(changes_df, output_path):
    """Create and save comprehensive change report."""
    print("\n" + "="*60)
    print("CREATING CHANGE REPORT")
    print("="*60)
    
    if changes_df.empty:
        print("No changes detected in ARCADIA_TR_ID")
        report_content = "No changes detected between old and new versions."
    else:
        # Create markdown report
        report_lines = [
            "# ARCADIA_TR_ID Change Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"- Total changes detected: {len(changes_df)}",
            ""
        ]
        
        # Add breakdown by type
        for change_type in changes_df['Change Type'].unique():
            count = len(changes_df[changes_df['Change Type'] == change_type])
            report_lines.append(f"- {change_type}: {count}")
        
        report_lines.extend([
            "",
            "## Detailed Changes",
            "",
            "| IG_ID | Target Name | Change Type | Old ARCADIA_TR_ID | New ARCADIA_TR_ID | Status |",
            "|-------|-------------|-------------|-------------------|-------------------|--------|"
        ])
        
        # Add each change
        for _, row in changes_df.iterrows():
            target_name = str(row['Target Name'])[:50]  # Truncate long names
            report_lines.append(
                f"| {row['IG_ID']} | {target_name} | {row['Change Type']} | "
                f"{row['Old ARCADIA_TR_ID']} | {row['New ARCADIA_TR_ID']} | {row['Status']} |"
            )
        
        report_content = "\n".join(report_lines)
    
    # Save report
    report_path = output_path / 'ARCADIA_ID_CHANGE_REPORT.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"[OK] Change report saved to: {report_path}")
    
    # Also save as CSV
    if not changes_df.empty:
        csv_path = output_path / 'arcadia_id_changes.csv'
        changes_df.to_csv(csv_path, index=False)
        print(f"[OK] Changes CSV saved to: {csv_path}")
    
    return report_content

def load_arcadia_database(file_path):
    """Load Arcadia database and prepare for mapping."""
    print("\n" + "="*60)
    print("LOADING ARCADIA DATABASE")
    print("="*60)
    
    df = load_csv_safely(file_path, "Arcadia Database")
    
    # Convert ID to string for consistent matching
    df['ID'] = df['ID'].astype(str)
    
    print(f"  Unique IDs in database: {df['ID'].nunique()}")
    
    # List columns that will be mapped
    arc_columns = [
        'Status*', 'Announcement date*', 'Target Company', 
        'Transaction Size*, $M', 'Transaction Type*', 'Transaction Category*',
        'closed date', 'To be closed', 'Lead Investor / Acquirer', 
        'Other Investors', 'Source URL*', 'Description*', 
        'source data', 'created at'
    ]
    
    print(f"  Columns to map: {len(arc_columns)}")
    
    return df, arc_columns

def update_arc_columns(df_main, df_arcadia, arc_columns):
    """Update ARC_* columns in main dataframe using ARCADIA_TR_ID."""
    print("\n" + "="*60)
    print("UPDATING ARC COLUMNS")
    print("="*60)
    
    # Convert ARCADIA_TR_ID to integer then string for matching
    # Handle NaN and float values properly
    def convert_id(val):
        if pd.isna(val) or val == '':
            return ''
        try:
            # Convert to int first to remove decimal, then to string
            return str(int(float(val)))
        except:
            return str(val)
    
    df_main['ARCADIA_TR_ID_str'] = df_main['ARCADIA_TR_ID'].apply(convert_id)
    
    # Initialize statistics
    updated_count = 0
    missing_count = 0
    
    # Map column names from Arcadia to ARC_* format
    column_mapping = {
        'Status*': 'ARC_Status*',
        'Announcement date*': 'ARC_Announcement date*',
        'Target Company': 'ARC_Target Company',
        'Transaction Size*, $M': 'ARC_Transaction Size*, $M',
        'Transaction Type*': 'ARC_Transaction Type*',
        'Transaction Category*': 'ARC_Transaction Category*',
        'closed date': 'ARC_closed date',
        'To be closed': 'ARC_To be closed',
        'Lead Investor / Acquirer': 'ARC_Lead Investor / Acquirer',
        'Other Investors': 'ARC_Other Investors',
        'Source URL*': 'ARC_Source URL*',
        'Description*': 'ARC_Description*',
        'source data': 'ARC_source data',
        'created at': 'ARC_created at'
    }
    
    # Create lookup dictionary from Arcadia database
    arcadia_lookup = df_arcadia.set_index('ID').to_dict('index')
    
    # Update each row with matching Arcadia data
    for idx, row in df_main.iterrows():
        arcadia_id = row['ARCADIA_TR_ID_str']
        
        # Skip empty IDs
        if arcadia_id == '' or arcadia_id == 'nan':
            continue
        
        # Look up in Arcadia database
        if arcadia_id in arcadia_lookup:
            arcadia_data = arcadia_lookup[arcadia_id]
            updated_count += 1
            
            # Update each ARC column
            for arc_col, arc_col_name in column_mapping.items():
                if arc_col in arcadia_data:
                    df_main.at[idx, arc_col_name] = arcadia_data[arc_col]
            
            # Also update ARCADIA_TR_URL
            df_main.at[idx, 'ARCADIA_TR_URL'] = f"https://arcadia.investgame.net/admin/transactions/transaction/{arcadia_id}/change/"
            
            # Set Human_checked status
            df_main.at[idx, 'Human_checked'] = 'UPDATED'
        else:
            missing_count += 1
            if pd.notna(row['ARCADIA_TR_ID']) and str(row['ARCADIA_TR_ID']) != '':
                print(f"  [WARNING] ARCADIA_TR_ID {arcadia_id} not found in database (IG_ID: {row.get('IG_ID', 'N/A')})")
    
    # Remove temporary column
    df_main = df_main.drop('ARCADIA_TR_ID_str', axis=1)
    
    print(f"\n[OK] Updated {updated_count} records with Arcadia data")
    print(f"[WARNING] {missing_count} ARCADIA_TR_IDs not found in database")
    
    return df_main, updated_count, missing_count

def validate_updates(df_main):
    """Validate the updated data."""
    print("\n" + "="*60)
    print("VALIDATING UPDATES")
    print("="*60)
    
    # Count records with ARCADIA_TR_ID
    has_arcadia_id = df_main['ARCADIA_TR_ID'].notna() & (df_main['ARCADIA_TR_ID'] != '')
    
    # Count records with ARC data
    has_arc_data = df_main['ARC_Status*'].notna()
    
    print(f"Records with ARCADIA_TR_ID: {has_arcadia_id.sum()}")
    print(f"Records with ARC data: {has_arc_data.sum()}")
    
    # Check consistency
    mismatch = has_arcadia_id & ~has_arc_data
    if mismatch.sum() > 0:
        print(f"[WARNING] {mismatch.sum()} records have ARCADIA_TR_ID but no ARC data")
        # Show first few examples
        examples = df_main[mismatch].head(5)[['IG_ID', 'Target name', 'ARCADIA_TR_ID']]
        print("\nExamples:")
        for _, row in examples.iterrows():
            print(f"  IG_ID: {row['IG_ID']}, Target: {row['Target name']}, ARCADIA_TR_ID: {row['ARCADIA_TR_ID']}")
    
    return has_arcadia_id.sum(), has_arc_data.sum()

def main():
    """Main execution function."""
    print("\n" + "="*80)
    print(" ARCADIA MAPPING ANALYSIS AND UPDATE")
    print(" Comparing changes and updating ARC columns")
    print("="*80)
    
    # Set paths
    base_path = Path(__file__).parent.parent
    output_path = base_path / 'output'
    src_path = base_path / 'src'
    archive_path = output_path / '_archive'
    
    # File paths
    new_file = output_path / 'ig_arc_mapping_full_vF.csv'
    old_file = archive_path / 'ig_arc_mapping_full_URL_REVIEWED_02-09-2025_vNew.csv'
    arcadia_db = src_path / 'arcadia_database_2025-09-03.csv'
    
    # Check files exist
    for file_path, name in [(new_file, "New version"), (old_file, "Old version"), (arcadia_db, "Arcadia database")]:
        if not file_path.exists():
            print(f"[ERROR] {name} not found: {file_path}")
            return 1
    
    try:
        # Phase 1: Load files
        print("\n" + "="*80)
        print(" PHASE 1: LOADING FILES")
        print("="*80)
        
        df_new = load_csv_safely(new_file, "New version (ig_arc_mapping_full_vF.csv)")
        df_old = load_csv_safely(old_file, "Old version (archive)")
        
        # Phase 2: Compare ARCADIA_TR_ID
        print("\n" + "="*80)
        print(" PHASE 2: COMPARING ARCADIA_TR_ID")
        print("="*80)
        
        changes_df = compare_arcadia_ids(df_old, df_new)
        
        # Create change report
        report_content = create_change_report(changes_df, output_path)
        
        # Print sample of changes
        if not changes_df.empty and len(changes_df) > 0:
            print("\nFirst 10 changes:")
            print(changes_df.head(10).to_string(index=False))
        
        # Phase 3: Update ARC columns
        print("\n" + "="*80)
        print(" PHASE 3: UPDATING ARC COLUMNS")
        print("="*80)
        
        df_arcadia, arc_columns = load_arcadia_database(arcadia_db)
        df_updated, updated_count, missing_count = update_arc_columns(df_new, df_arcadia, arc_columns)
        
        # Phase 4: Validate and save
        print("\n" + "="*80)
        print(" PHASE 4: VALIDATION AND SAVING")
        print("="*80)
        
        arcadia_count, arc_data_count = validate_updates(df_updated)
        
        # Save updated file
        output_file = output_path / f'ig_arc_mapping_full_UPDATED_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        df_updated.to_csv(output_file, index=False)
        print(f"\n[OK] Updated file saved to: {output_file}")
        
        # Try to overwrite the original vF file (may fail if file is open)
        try:
            df_updated.to_csv(new_file, index=False)
            print(f"[OK] Original file updated: {new_file}")
        except PermissionError:
            print(f"[WARNING] Could not update original file (may be open): {new_file}")
            print(f"         Please manually replace with: {output_file.name}")
        
        # Create final summary
        print("\n" + "="*80)
        print(" FINAL SUMMARY")
        print("="*80)
        print(f"ARCADIA_TR_ID changes detected: {len(changes_df)}")
        print(f"Records updated with ARC data: {updated_count}")
        print(f"Records with missing Arcadia data: {missing_count}")
        print(f"Total records with ARCADIA_TR_ID: {arcadia_count}")
        print(f"Total records with ARC data: {arc_data_count}")
        
        # Save summary
        summary = {
            'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'files_processed': {
                'new_version': str(new_file),
                'old_version': str(old_file),
                'arcadia_database': str(arcadia_db)
            },
            'changes_detected': len(changes_df),
            'records_updated': updated_count,
            'missing_arcadia_records': missing_count,
            'final_statistics': {
                'total_records': len(df_updated),
                'with_arcadia_id': int(arcadia_count),
                'with_arc_data': int(arc_data_count)
            }
        }
        
        summary_path = output_path / 'mapping_update_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n[OK] Summary saved to: {summary_path}")
        
        print("\n" + "="*80)
        print(" [OK] PROCESSING COMPLETED SUCCESSFULLY")
        print("="*80)
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())