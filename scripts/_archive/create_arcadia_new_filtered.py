#!/usr/bin/env python3
"""
Create arcadia_new.csv - Filtered Arcadia Database
===================================================
This script creates a filtered subset of db_arcadia_trx.csv by:
1. Removing transactions with Announcement Date before 2020-01-01
2. Removing transactions with IDs in verified_duplicate_arcadia_ids.json

Author: Data Analytics Team
Date: 02-09-2025
"""

import pandas as pd
import json
from datetime import datetime
import os

def load_data():
    """Load the source data files"""
    print("\n" + "="*80)
    print("CREATING FILTERED ARCADIA DATABASE - arcadia_new.csv")
    print("="*80)
    
    print("\n1. LOADING SOURCE DATA...")
    print("-" * 70)
    
    # Load main database
    db_path = 'output/db_arcadia_trx.csv'
    print(f"   Loading: {db_path}")
    df = pd.read_csv(db_path, encoding='utf-8')
    print(f"   [SUCCESS] Loaded {len(df):,} transactions from db_arcadia_trx.csv")
    
    # Load verified duplicate IDs
    ids_path = 'output/verified_duplicate_arcadia_ids.json'
    print(f"   Loading: {ids_path}")
    with open(ids_path, 'r') as f:
        verified_ids = json.load(f)
    print(f"   [SUCCESS] Loaded {len(verified_ids):,} verified duplicate IDs to exclude")
    
    return df, verified_ids

def filter_by_date(df):
    """Filter transactions to keep only those from 2020-01-01 onwards"""
    print("\n2. FILTERING BY ANNOUNCEMENT DATE...")
    print("-" * 70)
    
    initial_count = len(df)
    
    # Parse announcement dates
    df['Announcement date*'] = pd.to_datetime(df['Announcement date*'], errors='coerce')
    
    # Count valid dates
    valid_dates = df['Announcement date*'].notna().sum()
    print(f"   Valid dates: {valid_dates:,}/{initial_count:,} ({valid_dates/initial_count*100:.1f}%)")
    
    # Define cutoff date
    cutoff_date = pd.Timestamp('2020-01-01')
    print(f"   Cutoff date: {cutoff_date.date()}")
    
    # Count transactions before cutoff
    before_cutoff = (df['Announcement date*'] < cutoff_date).sum()
    print(f"   Transactions before cutoff: {before_cutoff:,}")
    
    # Filter to keep only transactions from 2020-01-01 onwards
    # Keep rows where date is >= cutoff OR date is null (to be conservative)
    df_filtered = df[(df['Announcement date*'] >= cutoff_date) | df['Announcement date*'].isna()].copy()
    
    removed_count = initial_count - len(df_filtered)
    print(f"   [DONE] Removed {removed_count:,} transactions before 2020-01-01")
    print(f"   Remaining: {len(df_filtered):,} transactions")
    
    return df_filtered

def filter_by_verified_ids(df, verified_ids):
    """Remove transactions with IDs in the verified duplicate list"""
    print("\n3. REMOVING VERIFIED DUPLICATE IDS...")
    print("-" * 70)
    
    initial_count = len(df)
    
    # Convert verified_ids to set for faster lookup
    verified_ids_set = set(verified_ids)
    print(f"   IDs to exclude: {len(verified_ids_set):,}")
    
    # Count how many will be removed
    ids_to_remove = df['ID'].isin(verified_ids_set).sum()
    print(f"   Transactions matching exclusion list: {ids_to_remove:,}")
    
    # Filter out the verified IDs
    df_filtered = df[~df['ID'].isin(verified_ids_set)].copy()
    
    removed_count = initial_count - len(df_filtered)
    print(f"   [DONE] Removed {removed_count:,} transactions with verified IDs")
    print(f"   Remaining: {len(df_filtered):,} transactions")
    
    return df_filtered

def save_filtered_data(df):
    """Save the filtered dataframe"""
    print("\n4. SAVING FILTERED DATA...")
    print("-" * 70)
    
    output_path = 'output/arcadia_new.csv'
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"   [DONE] Saved {len(df):,} transactions to: {output_path}")
    
    # Calculate file size
    file_size = os.path.getsize(output_path) / (1024 * 1024)  # Convert to MB
    print(f"   File size: {file_size:.2f} MB")
    
    return output_path

def generate_summary_report(df_original, df_filtered, verified_ids):
    """Generate a detailed summary report"""
    print("\n5. SUMMARY REPORT...")
    print("-" * 70)
    
    # Calculate statistics
    original_count = len(df_original)
    filtered_count = len(df_filtered)
    
    # Date filtering stats
    df_original['Announcement date*'] = pd.to_datetime(df_original['Announcement date*'], errors='coerce')
    cutoff_date = pd.Timestamp('2020-01-01')
    removed_by_date = (df_original['Announcement date*'] < cutoff_date).sum()
    
    # ID filtering stats
    verified_ids_set = set(verified_ids)
    removed_by_id_before_date_filter = df_original['ID'].isin(verified_ids_set).sum()
    
    # After date filter
    df_after_date = df_original[(df_original['Announcement date*'] >= cutoff_date) | df_original['Announcement date*'].isna()]
    removed_by_id_after_date_filter = df_after_date['ID'].isin(verified_ids_set).sum()
    
    print("\n   FILTERING SUMMARY:")
    print("   " + "="*50)
    print(f"   Original transactions:        {original_count:,}")
    print(f"   Removed by date (<2020):     -{removed_by_date:,}")
    print(f"   After date filter:            {len(df_after_date):,}")
    print(f"   Removed by verified IDs:     -{removed_by_id_after_date_filter:,}")
    print(f"   Final transactions:           {filtered_count:,}")
    print("   " + "="*50)
    print(f"   Total removed:                {original_count - filtered_count:,}")
    print(f"   Reduction percentage:         {(original_count - filtered_count)/original_count*100:.1f}%")
    
    # Date range of final dataset
    if filtered_count > 0:
        df_filtered['Announcement date*'] = pd.to_datetime(df_filtered['Announcement date*'], errors='coerce')
        valid_dates = df_filtered['Announcement date*'].dropna()
        if len(valid_dates) > 0:
            print(f"\n   Date range in final dataset:")
            print(f"   Earliest: {valid_dates.min().date()}")
            print(f"   Latest:   {valid_dates.max().date()}")
    
    # Company statistics
    print(f"\n   Company statistics:")
    print(f"   Unique companies: {df_filtered['Target Company'].nunique():,}")
    
    # Transaction size statistics
    print(f"\n   Transaction size statistics:")
    sizes = df_filtered['Transaction Size*, $M'].dropna()
    if len(sizes) > 0:
        print(f"   Total value: ${sizes.sum():,.1f}M")
        print(f"   Average size: ${sizes.mean():,.1f}M")
        print(f"   Median size: ${sizes.median():,.1f}M")
    
    # Save summary to file
    summary = {
        'creation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'original_count': int(original_count),
        'filtered_count': int(filtered_count),
        'removed_by_date': int(removed_by_date),
        'removed_by_verified_ids': int(removed_by_id_after_date_filter),
        'total_removed': int(original_count - filtered_count),
        'reduction_percentage': round((original_count - filtered_count)/original_count*100, 2),
        'verified_ids_count': len(verified_ids),
        'unique_companies': int(df_filtered['Target Company'].nunique()),
        'date_range': {
            'min': str(valid_dates.min().date()) if len(valid_dates) > 0 else None,
            'max': str(valid_dates.max().date()) if len(valid_dates) > 0 else None
        }
    }
    
    summary_path = 'output/arcadia_new_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\n   [DONE] Summary saved to: {summary_path}")
    
    return summary

def main():
    """Main execution"""
    try:
        # Load data
        df_original, verified_ids = load_data()
        
        # Store original for comparison
        df_filtered = df_original.copy()
        
        # Apply filters
        df_filtered = filter_by_date(df_filtered)
        df_filtered = filter_by_verified_ids(df_filtered, verified_ids)
        
        # Save filtered data
        output_path = save_filtered_data(df_filtered)
        
        # Generate summary report
        summary = generate_summary_report(df_original, df_filtered, verified_ids)
        
        print("\n" + "="*80)
        print("PROCESS COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"\n[SUCCESS] Created: arcadia_new.csv")
        print(f"[SUCCESS] Final record count: {len(df_filtered):,} transactions")
        print(f"[SUCCESS] Ready for matching with investgame_new.csv")
        
        return df_filtered, summary
        
    except Exception as e:
        print(f"\n[ERROR]: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    df_filtered, summary = main()