#!/usr/bin/env python3
"""
Script to apply updated mappings to unmapped IG data
Created: 2025-09-03
Purpose: Update type and category mappings according to new Arcadia rules

Key changes:
1. Series A+ → undisclosed early-stage
2. Series B+, G, H → undisclosed late-stage  
3. Category names: "Investments" → "investment" (lowercase, singular)
4. M&A category updates based on type changes
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

def create_before_snapshot(df):
    """Create a snapshot of current state for comparison"""
    snapshot = df[['IG_ID', 'Target name', 'Type', 'Category', 'Mapped_Type', 'Mapped_Category']].copy()
    return snapshot

def apply_updated_type_mappings(df):
    """Apply the updated type mappings according to new rules"""
    
    print("\n=== APPLYING UPDATED TYPE MAPPINGS ===")
    print("-" * 50)
    
    # Complete type mapping dictionary with updates
    type_mapping = {
        # Early-Stage Types
        'Seed round': 'seed',
        'Grant': 'accelerator / grant',
        'Accelerator/Incubator': 'accelerator / grant',
        'Series A': 'series a',
        'Series A+': 'undisclosed early-stage',  # UPDATED
        
        # Late-Stage Types
        'Series B': 'series b',
        'Series B+': 'undisclosed late-stage',  # UPDATED
        'Series C': 'series c',
        'Series D': 'series d',
        'Series D+': 'series d',
        'Series E': 'series e',
        'Series G': 'undisclosed late-stage',  # UPDATED
        'Series H': 'undisclosed late-stage',  # UPDATED
        'Growth': 'growth / expansion (not specified)',
        'Fixed Income': 'fixed income',
        'Fixed income': 'fixed income',
        
        # M&A Types
        'Control': 'm&a control (incl. lbo/mbo)',
        'Control ': 'm&a control (incl. lbo/mbo)',  # With trailing space
        'Minority': 'm&a minority',
        
        # Public Offering Types
        'IPO': 'listing (ipo/spac)',
        'SPAC': 'listing (ipo/spac)',
        'Direct Listing': 'listing (ipo/spac)',
        'PIPE': 'pipe',
        'PIPE, Other': 'pipe',
        'PIPE, other': 'pipe',
        
        # Generic/Undefined
        'Undisclosed': 'undisclosed early-stage',
        'Late-stage': 'undisclosed late-stage',
    }
    
    # Track changes
    changes_made = 0
    
    # Apply type mappings for non-Corporate transactions
    non_corporate_mask = df['Type'] != 'Corporate'
    
    for idx in df[non_corporate_mask].index:
        original_type = df.at[idx, 'Type']
        
        if original_type in type_mapping:
            new_type = type_mapping[original_type]
            if df.at[idx, 'Mapped_Type'] != new_type:
                df.at[idx, 'Mapped_Type'] = new_type
                changes_made += 1
    
    print(f"Type mappings updated: {changes_made} records")
    
    return df

def update_category_names(df):
    """Update category names to match Arcadia format (investment vs Investments)"""
    
    print("\n=== UPDATING CATEGORY NAMES ===")
    print("-" * 50)
    
    # Category name mapping
    category_mapping = {
        'Early-stage Investments': 'Early-stage investment',
        'Late-stage Investments': 'Late-stage investment',
        'M&A': 'M&A',  # Stays the same
        'Public offering': 'Public offering',  # Stays the same
        'Corporate': 'Corporate',  # Should not exist after mapping
    }
    
    changes_made = 0
    
    for idx in df.index:
        current_cat = df.at[idx, 'Mapped_Category']
        if current_cat in category_mapping:
            new_cat = category_mapping[current_cat]
            if current_cat != new_cat:
                df.at[idx, 'Mapped_Category'] = new_cat
                changes_made += 1
    
    print(f"Category names updated: {changes_made} records")
    
    return df

def determine_category_from_type(mapped_type):
    """Determine category based on the mapped type"""
    
    # M&A types
    if any(x in mapped_type.lower() for x in ['m&a', 'control', 'minority']):
        return 'M&A'
    
    # Public offering types
    elif any(x in mapped_type.lower() for x in ['listing', 'ipo', 'spac', 'pipe', 'fixed income']):
        return 'Public offering'
    
    # Late-stage types
    elif any(x in mapped_type.lower() for x in ['series b', 'series c', 'series d', 'series e', 
                                                 'growth', 'expansion', 'undisclosed late-stage']):
        return 'Late-stage investment'
    
    # Early-stage types (default)
    else:
        return 'Early-stage investment'

def update_categories_based_on_types(df):
    """Update categories based on the new type mappings"""
    
    print("\n=== UPDATING CATEGORIES BASED ON NEW TYPES ===")
    print("-" * 50)
    
    changes_made = 0
    
    # Don't override M&A category if it was originally M&A
    # But DO update other categories based on new type mappings
    for idx in df.index:
        mapped_type = df.at[idx, 'Mapped_Type']
        original_category = df.at[idx, 'Category']
        current_mapped_category = df.at[idx, 'Mapped_Category']
        
        # Determine what the category should be based on type
        expected_category = determine_category_from_type(mapped_type)
        
        # Update if different
        if current_mapped_category != expected_category:
            df.at[idx, 'Mapped_Category'] = expected_category
            changes_made += 1
    
    print(f"Categories updated based on types: {changes_made} records")
    
    return df

def generate_change_report(before_snapshot, after_df):
    """Generate detailed report of changes"""
    
    print("\n=== CHANGE ANALYSIS REPORT ===")
    print("=" * 70)
    
    # Merge before and after for comparison
    after_snapshot = after_df[['IG_ID', 'Target name', 'Type', 'Category', 'Mapped_Type', 'Mapped_Category']].copy()
    
    # Find changes
    type_changes = []
    category_changes = []
    
    for idx in range(len(before_snapshot)):
        before_row = before_snapshot.iloc[idx]
        after_row = after_snapshot.iloc[idx]
        
        if before_row['Mapped_Type'] != after_row['Mapped_Type']:
            type_changes.append({
                'IG_ID': before_row['IG_ID'],
                'Target': before_row['Target name'],
                'Original_Type': before_row['Type'],
                'Before_Mapped': before_row['Mapped_Type'],
                'After_Mapped': after_row['Mapped_Type']
            })
        
        if before_row['Mapped_Category'] != after_row['Mapped_Category']:
            category_changes.append({
                'IG_ID': before_row['IG_ID'],
                'Target': before_row['Target name'],
                'Before_Category': before_row['Mapped_Category'],
                'After_Category': after_row['Mapped_Category']
            })
    
    print(f"\nTotal Type Changes: {len(type_changes)}")
    print(f"Total Category Changes: {len(category_changes)}")
    
    # Show specific changes for Series A+, B+, G, H
    print("\n=== SPECIFIC SERIES CHANGES ===")
    series_of_interest = ['Series A+', 'Series B+', 'Series G', 'Series H']
    
    for series_type in series_of_interest:
        series_mask = after_df['Type'] == series_type
        series_count = series_mask.sum()
        
        if series_count > 0:
            series_df = after_df[series_mask]
            print(f"\n{series_type}: {series_count} transactions")
            print(f"  Mapped Type: {series_df['Mapped_Type'].iloc[0]}")
            print(f"  Mapped Category: {series_df['Mapped_Category'].iloc[0]}")
    
    return type_changes, category_changes

def create_audit_log(type_changes, category_changes, output_dir):
    """Create detailed audit log of all changes"""
    
    audit_file = output_dir / f'mapping_update_audit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    
    with open(audit_file, 'w', encoding='utf-8') as f:
        f.write("MAPPING UPDATE AUDIT LOG\n")
        f.write("=" * 70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Script: apply_updated_mappings.py\n\n")
        
        f.write("TYPE MAPPING CHANGES\n")
        f.write("-" * 70 + "\n")
        
        if type_changes:
            for change in type_changes:
                f.write(f"ID: {change['IG_ID']} | {change['Target']}\n")
                f.write(f"  Original Type: {change['Original_Type']}\n")
                f.write(f"  Before Mapping: {change['Before_Mapped']}\n")
                f.write(f"  After Mapping: {change['After_Mapped']}\n\n")
        else:
            f.write("No type mapping changes\n\n")
        
        f.write("CATEGORY CHANGES\n")
        f.write("-" * 70 + "\n")
        
        if category_changes:
            for change in category_changes:
                f.write(f"ID: {change['IG_ID']} | {change['Target']}\n")
                f.write(f"  Before: {change['Before_Category']}\n")
                f.write(f"  After: {change['After_Category']}\n\n")
        else:
            f.write("No category changes\n\n")
    
    print(f"\nAudit log saved: {audit_file}")
    
    return audit_file

def main():
    """Main execution function"""
    
    print("=" * 70)
    print("APPLYING UPDATED MAPPINGS TO UNMAPPED IG DATA")
    print("=" * 70)
    
    # File paths
    input_file = Path('../output/ig_arc_unmapped_cleaned.csv')
    output_file = Path('../output/ig_arc_unmapped_final.csv')
    output_dir = Path('../output')
    
    # Read the cleaned file
    print(f"\n1. Reading file: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"   Total records: {len(df)}")
    
    # Create before snapshot
    print("\n2. Creating before snapshot for comparison")
    before_snapshot = create_before_snapshot(df)
    
    # Apply updated type mappings
    print("\n3. Applying updated type mappings")
    df = apply_updated_type_mappings(df)
    
    # Update category names (Investments → investment)
    print("\n4. Updating category names to Arcadia format")
    df = update_category_names(df)
    
    # Update categories based on new type mappings
    print("\n5. Updating categories based on new types")
    df = update_categories_based_on_types(df)
    
    # Generate change report
    print("\n6. Generating change report")
    type_changes, category_changes = generate_change_report(before_snapshot, df)
    
    # Create audit log
    print("\n7. Creating audit log")
    audit_file = create_audit_log(type_changes, category_changes, output_dir)
    
    # Save the updated file
    print(f"\n8. Saving updated file: {output_file}")
    df.to_csv(output_file, index=False, encoding='utf-8')
    print("   File saved successfully!")
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    
    print("\nCategory Distribution After Updates:")
    category_counts = df['Mapped_Category'].value_counts()
    for cat, count in category_counts.items():
        print(f"  {cat}: {count}")
    
    print("\nType Distribution (Top 10):")
    type_counts = df['Mapped_Type'].value_counts().head(10)
    for typ, count in type_counts.items():
        print(f"  {typ}: {count}")
    
    print("\n" + "=" * 70)
    print("MAPPING UPDATE COMPLETE!")
    print("=" * 70)
    
    # Return summary statistics
    return {
        'total_records': len(df),
        'type_changes': len(type_changes),
        'category_changes': len(category_changes),
        'output_file': str(output_file),
        'audit_file': str(audit_file)
    }

if __name__ == "__main__":
    summary = main()