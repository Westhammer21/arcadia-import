#!/usr/bin/env python3
"""
Clean Pre-2020 Transactions from Arcadia Missing Mapping
=========================================================
Removes transactions with Announcement date OR closed date before 2020-01-01
since InvestGame database doesn't track pre-2020 transactions.

Author: AI Analytics Team
Date: 2025-09-02
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json
import sys

def load_arcadia_missing_mapping(file_path):
    """Load the arcadia_missing_mapping.csv file with proper delimiter detection."""
    print("\n" + "="*60)
    print("STEP 1-3: Loading and Analyzing File Structure")
    print("="*60)
    
    # Try to detect delimiter
    with open(file_path, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        second_line = f.readline()
    
    # Check if tab-separated
    if '\t' in first_line:
        print("[OK] Detected TAB-separated file")
        delimiter = '\t'
    else:
        print("[OK] Detected COMMA-separated file")
        delimiter = ','
    
    # Load the CSV
    df = pd.read_csv(file_path, delimiter=delimiter, encoding='utf-8')
    
    print(f"[OK] Successfully loaded file with {len(df)} rows")
    print(f"[OK] Number of columns: {len(df.columns)}")
    
    return df, delimiter

def analyze_columns(df):
    """Analyze column names for case sensitivity and date columns."""
    print("\n" + "="*60)
    print("STEP 4-6: Analyzing Columns and Date Formats")
    print("="*60)
    
    # Print all column names
    print("\nColumn names found:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. '{col}'")
    
    # Find date columns (case-insensitive search)
    date_columns = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'announcement' in col_lower and 'date' in col_lower:
            date_columns['announcement'] = col
            print(f"\n[OK] Found Announcement date column: '{col}'")
        elif 'closed' in col_lower and 'date' in col_lower:
            date_columns['closed'] = col
            print(f"[OK] Found Closed date column: '{col}'")
    
    if not date_columns.get('announcement'):
        print("[WARNING] Could not find Announcement date column")
    if not date_columns.get('closed'):
        print("[WARNING] Could not find Closed date column")
    
    return date_columns

def analyze_date_patterns(df, date_columns):
    """Analyze date format patterns in the date columns."""
    print("\n" + "="*60)
    print("STEP 6: Analyzing Date Format Patterns")
    print("="*60)
    
    for date_type, col_name in date_columns.items():
        if col_name and col_name in df.columns:
            print(f"\n{date_type.title()} Date Column ('{col_name}'):")
            
            # Sample values
            sample_values = df[col_name].dropna().head(10)
            print(f"  Sample values:")
            for val in sample_values:
                print(f"    - {val}")
            
            # Count non-null values
            non_null_count = df[col_name].notna().sum()
            null_count = df[col_name].isna().sum()
            print(f"  Non-null values: {non_null_count}")
            print(f"  Null/missing values: {null_count}")

def parse_dates(df, date_columns):
    """Parse date columns with DD/MM/YYYY format."""
    print("\n" + "="*60)
    print("STEP 9-12: Parsing Date Columns")
    print("="*60)
    
    parsed_dates = {}
    
    for date_type, col_name in date_columns.items():
        if col_name and col_name in df.columns:
            print(f"\nParsing {date_type} dates from column '{col_name}'...")
            
            # Create a new column for parsed dates
            parsed_col_name = f"{col_name}_parsed"
            
            # Parse dates with DD/MM/YYYY format
            df[parsed_col_name] = pd.to_datetime(
                df[col_name], 
                format='%d/%m/%Y', 
                errors='coerce',
                dayfirst=True
            )
            
            # Count successful parses
            successful_parses = df[parsed_col_name].notna().sum()
            failed_parses = df[parsed_col_name].isna().sum() - df[col_name].isna().sum()
            
            print(f"  [OK] Successfully parsed: {successful_parses} dates")
            if failed_parses > 0:
                print(f"  [WARNING] Failed to parse: {failed_parses} dates")
                # Show examples of failed parses
                failed_mask = df[parsed_col_name].isna() & df[col_name].notna()
                if failed_mask.any():
                    print(f"  Examples of unparseable dates:")
                    failed_examples = df.loc[failed_mask, col_name].head(5)
                    for val in failed_examples:
                        print(f"    - '{val}'")
            
            parsed_dates[date_type] = parsed_col_name
    
    return df, parsed_dates

def identify_pre2020_transactions(df, parsed_dates):
    """Identify transactions with dates before 2020-01-01."""
    print("\n" + "="*60)
    print("STEP 13-17: Identifying Pre-2020 Transactions")
    print("="*60)
    
    cutoff_date = pd.Timestamp('2020-01-01')
    print(f"\nCutoff date: {cutoff_date.strftime('%Y-%m-%d')}")
    
    # Initialize masks
    pre2020_announcement = pd.Series([False] * len(df))
    pre2020_closed = pd.Series([False] * len(df))
    
    # Check announcement dates
    if 'announcement' in parsed_dates:
        col = parsed_dates['announcement']
        pre2020_announcement = df[col] < cutoff_date
        count_pre2020_announcement = pre2020_announcement.sum()
        print(f"\n[OK] Found {count_pre2020_announcement} transactions with Announcement date < 2020-01-01")
        
        # Show examples
        if count_pre2020_announcement > 0:
            print("  Examples:")
            examples = df[pre2020_announcement].head(3)
            for idx, row in examples.iterrows():
                date_str = row[col].strftime('%d/%m/%Y') if pd.notna(row[col]) else 'N/A'
                print(f"    - ID {row.get('ID', 'N/A')}: {date_str}")
    
    # Check closed dates
    if 'closed' in parsed_dates:
        col = parsed_dates['closed']
        pre2020_closed = df[col] < cutoff_date
        count_pre2020_closed = pre2020_closed.sum()
        print(f"\n[OK] Found {count_pre2020_closed} transactions with Closed date < 2020-01-01")
        
        # Show examples
        if count_pre2020_closed > 0:
            print("  Examples:")
            examples = df[pre2020_closed].head(3)
            for idx, row in examples.iterrows():
                date_str = row[col].strftime('%d/%m/%Y') if pd.notna(row[col]) else 'N/A'
                print(f"    - ID {row.get('ID', 'N/A')}: {date_str}")
    
    # Combine with OR logic
    pre2020_mask = pre2020_announcement | pre2020_closed
    total_pre2020 = pre2020_mask.sum()
    
    print(f"\n[OK] TOTAL transactions to remove (OR logic): {total_pre2020}")
    print(f"  - Only Announcement < 2020: {(pre2020_announcement & ~pre2020_closed).sum()}")
    print(f"  - Only Closed < 2020: {(~pre2020_announcement & pre2020_closed).sum()}")
    print(f"  - Both dates < 2020: {(pre2020_announcement & pre2020_closed).sum()}")
    
    return pre2020_mask, pre2020_announcement, pre2020_closed

def create_removal_report(df, pre2020_mask, pre2020_announcement, pre2020_closed, date_columns, parsed_dates):
    """Create detailed report of transactions to be removed."""
    print("\n" + "="*60)
    print("STEP 17: Creating Removal Report")
    print("="*60)
    
    removal_df = df[pre2020_mask].copy()
    
    # Add removal reason
    reasons = []
    for idx in removal_df.index:
        reason_parts = []
        if pre2020_announcement.loc[idx]:
            reason_parts.append("Announcement < 2020")
        if pre2020_closed.loc[idx]:
            reason_parts.append("Closed < 2020")
        reasons.append(" & ".join(reason_parts))
    
    removal_df['Removal_Reason'] = reasons
    
    # Select relevant columns for report
    report_columns = ['ID'] if 'ID' in df.columns else []
    if date_columns.get('announcement'):
        report_columns.append(date_columns['announcement'])
    if date_columns.get('closed'):
        report_columns.append(date_columns['closed'])
    report_columns.extend(['Target Company', 'Transaction Size*, $M', 'Removal_Reason'])
    
    # Filter to existing columns
    report_columns = [col for col in report_columns if col in removal_df.columns]
    
    removal_report = removal_df[report_columns]
    
    # Save removal report
    report_path = Path(__file__).parent.parent / 'output' / 'pre2020_removal_report.csv'
    removal_report.to_csv(report_path, index=False)
    print(f"\n[OK] Removal report saved to: {report_path}")
    print(f"  Total transactions to remove: {len(removal_report)}")
    
    return removal_report

def apply_filter_and_save(df, pre2020_mask, delimiter, original_path):
    """Apply filter to remove pre-2020 transactions and save results."""
    print("\n" + "="*60)
    print("STEP 18-22: Applying Filter and Saving Results")
    print("="*60)
    
    # Count before and after
    rows_before = len(df)
    
    # Apply filter (keep only post-2020 transactions)
    df_filtered = df[~pre2020_mask].copy()
    rows_after = len(df_filtered)
    
    print(f"\nFiltering Results:")
    print(f"  Rows before filtering: {rows_before}")
    print(f"  Rows removed: {rows_before - rows_after}")
    print(f"  Rows after filtering: {rows_after}")
    print(f"  Reduction: {((rows_before - rows_after) / rows_before * 100):.1f}%")
    
    # Remove the parsed date columns before saving
    parsed_cols = [col for col in df_filtered.columns if col.endswith('_parsed')]
    df_filtered = df_filtered.drop(columns=parsed_cols)
    
    # Save cleaned file
    output_path = Path(__file__).parent.parent / 'output' / 'arcadia_missing_mapping_cleaned.csv'
    df_filtered.to_csv(output_path, sep=delimiter, index=False)
    print(f"\n[OK] Cleaned file saved to: {output_path}")
    
    # Create backup of original
    backup_path = Path(__file__).parent.parent / 'output' / f'arcadia_missing_mapping_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    df.drop(columns=parsed_cols, errors='ignore').to_csv(backup_path, sep=delimiter, index=False)
    print(f"[OK] Backup of original saved to: {backup_path}")
    
    return df_filtered, rows_before, rows_after

def validate_results(df_filtered, parsed_dates, date_columns):
    """Validate that no 2020+ transactions were removed."""
    print("\n" + "="*60)
    print("STEP 20-21: Validating Results")
    print("="*60)
    
    cutoff_date = pd.Timestamp('2020-01-01')
    
    # Re-parse dates in filtered dataframe
    for date_type, col_name in date_columns.items():
        if col_name and col_name in df_filtered.columns:
            parsed_col = f"{col_name}_check"
            df_filtered[parsed_col] = pd.to_datetime(
                df_filtered[col_name], 
                format='%d/%m/%Y', 
                errors='coerce',
                dayfirst=True
            )
            
            # Check if any remaining dates are pre-2020
            if parsed_col in df_filtered.columns:
                pre2020_remaining = (df_filtered[parsed_col] < cutoff_date).sum()
                if pre2020_remaining > 0:
                    print(f"\n[WARNING] Found {pre2020_remaining} pre-2020 {date_type} dates still in filtered data!")
                else:
                    print(f"\n[OK] Validation passed: No pre-2020 {date_type} dates in filtered data")
    
    # Sample validation
    print("\n[OK] Random sample of remaining transactions:")
    sample_size = min(5, len(df_filtered))
    sample = df_filtered.sample(n=sample_size) if len(df_filtered) > 0 else df_filtered
    
    for idx, row in sample.iterrows():
        id_val = row.get('ID', 'N/A')
        target = row.get('Target Company', 'N/A')
        print(f"  - ID {id_val}: {target}")

def create_summary_report(rows_before, rows_after, pre2020_announcement_count, pre2020_closed_count, pre2020_both_count):
    """Create and save summary report."""
    print("\n" + "="*60)
    print("STEP 23: Creating Summary Report")
    print("="*60)
    
    summary = {
        "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "original_file": "arcadia_missing_mapping.csv",
        "cleaned_file": "arcadia_missing_mapping_cleaned.csv",
        "statistics": {
            "rows_before": int(rows_before),
            "rows_after": int(rows_after),
            "rows_removed": int(rows_before - rows_after),
            "reduction_percentage": round((rows_before - rows_after) / rows_before * 100, 2)
        },
        "removal_breakdown": {
            "announcement_date_only": int(pre2020_announcement_count),
            "closed_date_only": int(pre2020_closed_count),
            "both_dates": int(pre2020_both_count),
            "total": int(pre2020_announcement_count + pre2020_closed_count - pre2020_both_count)
        },
        "cutoff_date": "2020-01-01",
        "reason": "InvestGame database does not track pre-2020 transactions"
    }
    
    # Save summary as JSON
    summary_path = Path(__file__).parent.parent / 'output' / 'pre2020_cleanup_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n[OK] Summary report saved to: {summary_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Original rows: {summary['statistics']['rows_before']}")
    print(f"Cleaned rows: {summary['statistics']['rows_after']}")
    print(f"Removed rows: {summary['statistics']['rows_removed']}")
    print(f"Reduction: {summary['statistics']['reduction_percentage']}%")
    
    return summary

def main():
    """Main execution function."""
    print("\n" + "="*80)
    print(" PRE-2020 TRANSACTION CLEANUP SCRIPT")
    print(" Removing Arcadia transactions before 2020-01-01")
    print("="*80)
    
    # File path
    file_path = Path(__file__).parent.parent / 'output' / 'arcadia_missing_mapping.csv'
    
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return 1
    
    try:
        # Step 1-3: Load file
        df, delimiter = load_arcadia_missing_mapping(file_path)
        
        # Step 4-5: Analyze columns
        date_columns = analyze_columns(df)
        
        # Step 6: Analyze date patterns
        analyze_date_patterns(df, date_columns)
        
        # Step 7: Count total rows
        print(f"\n[OK] Total rows before filtering: {len(df)}")
        
        # Step 9-12: Parse dates
        df, parsed_dates = parse_dates(df, date_columns)
        
        # Step 13-17: Identify pre-2020 transactions
        pre2020_mask, pre2020_announcement, pre2020_closed = identify_pre2020_transactions(df, parsed_dates)
        
        # Calculate breakdown
        pre2020_announcement_count = (pre2020_announcement & ~pre2020_closed).sum()
        pre2020_closed_count = (~pre2020_announcement & pre2020_closed).sum()
        pre2020_both_count = (pre2020_announcement & pre2020_closed).sum()
        
        # Step 17: Create removal report
        removal_report = create_removal_report(df, pre2020_mask, pre2020_announcement, pre2020_closed, date_columns, parsed_dates)
        
        # Step 18-22: Apply filter and save
        df_filtered, rows_before, rows_after = apply_filter_and_save(df, pre2020_mask, delimiter, file_path)
        
        # Step 20-21: Validate results
        validate_results(df_filtered, parsed_dates, date_columns)
        
        # Step 23: Create summary report
        summary = create_summary_report(rows_before, rows_after, pre2020_announcement_count, pre2020_closed_count, pre2020_both_count)
        
        print("\n" + "="*80)
        print(" [OK] CLEANUP COMPLETED SUCCESSFULLY")
        print("="*80)
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())