#!/usr/bin/env python3
"""
Script to map Corporate transactions in unmapped IG data according to Arcadia rules
Created: 2025-09-03
Purpose: Clean up ig_arc_unmapped.csv by properly mapping Corporate transactions
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

def analyze_corporate_transactions():
    """Analyze and map Corporate transactions according to Arcadia rules"""
    
    # File paths
    input_file = Path('../output/ig_arc_unmapped.csv')
    backup_file = Path('../output/ig_arc_unmapped_BACKUP_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv')
    output_file = Path('../output/ig_arc_unmapped_cleaned.csv')
    
    print("=" * 70)
    print("CORPORATE TRANSACTION MAPPING FOR UNMAPPED IG DATA")
    print("=" * 70)
    
    # Read the unmapped transactions file
    print(f"\n1. Reading file: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"   Total records: {len(df)}")
    print(f"   Total columns: {len(df.columns)}")
    
    # Create backup
    print(f"\n2. Creating backup: {backup_file}")
    df.to_csv(backup_file, index=False, encoding='utf-8')
    print("   Backup created successfully")
    
    # Analyze Corporate transactions
    print("\n3. CORPORATE TRANSACTIONS ANALYSIS")
    print("-" * 50)
    
    # Find Corporate transactions (case-sensitive)
    corporate_type = df[df['Type'] == 'Corporate']
    corporate_cat = df[df['Category'] == 'Corporate']
    both_corporate = df[(df['Type'] == 'Corporate') | (df['Category'] == 'Corporate')]
    
    print(f"   Type = 'Corporate': {len(corporate_type)} transactions")
    print(f"   Category = 'Corporate': {len(corporate_cat)} transactions")
    print(f"   Either Type OR Category = 'Corporate': {len(both_corporate)} transactions")
    
    # Check overlap
    overlap = df[(df['Type'] == 'Corporate') & (df['Category'] == 'Corporate')]
    print(f"   BOTH Type AND Category = 'Corporate': {len(overlap)} transactions")
    
    # Analyze Size distribution for Corporate
    print("\n4. SIZE DISTRIBUTION FOR CORPORATE TRANSACTIONS")
    print("-" * 50)
    
    corp_df = both_corporate.copy()
    
    # Size analysis
    size_col = 'Size, $m'
    corp_with_size = corp_df[corp_df[size_col] > 0]
    corp_no_size = corp_df[(corp_df[size_col].isna()) | (corp_df[size_col] == 0)]
    
    print(f"   With known size (>0): {len(corp_with_size)} transactions")
    print(f"   Without size (0 or null): {len(corp_no_size)} transactions")
    
    if len(corp_with_size) > 0:
        print(f"\n   Size distribution for Corporate with known size:")
        print(f"   - Size <= $5M: {len(corp_with_size[corp_with_size[size_col] <= 5])} transactions")
        print(f"   - Size $5.01-10M: {len(corp_with_size[(corp_with_size[size_col] > 5) & (corp_with_size[size_col] <= 10)])} transactions")
        print(f"   - Size > $10M: {len(corp_with_size[corp_with_size[size_col] > 10])} transactions")
    
    # Company age analysis
    print("\n5. COMPANY AGE ANALYSIS FOR CORPORATE WITHOUT SIZE")
    print("-" * 50)
    
    if len(corp_no_size) > 0:
        # Calculate ages for transactions without size
        corp_no_size_copy = corp_no_size.copy()
        
        # Extract year from Date column
        corp_no_size_copy['Transaction_Year'] = pd.to_datetime(corp_no_size_copy['Date'], format='%d/%m/%Y').dt.year
        
        # Calculate company age
        corp_no_size_copy['Company_Age'] = corp_no_size_copy.apply(
            lambda row: row['Transaction_Year'] - row['Target Founded'] 
            if pd.notna(row['Target Founded']) and row['Target Founded'] > 0 
            else np.nan, axis=1
        )
        
        with_age = corp_no_size_copy[corp_no_size_copy['Company_Age'].notna()]
        no_age = corp_no_size_copy[corp_no_size_copy['Company_Age'].isna()]
        
        print(f"   With age data: {len(with_age)} transactions")
        print(f"   Without age data: {len(no_age)} transactions")
        
        if len(with_age) > 0:
            young = with_age[with_age['Company_Age'] <= 3]
            mature = with_age[with_age['Company_Age'] > 3]
            print(f"   - Age <= 3 years: {len(young)} transactions")
            print(f"   - Age > 3 years: {len(mature)} transactions")
    
    print("\n6. MAPPING SUMMARY PREVIEW")
    print("-" * 50)
    print("   Corporate transactions will be mapped as follows:")
    print("   - Size <= $5M -> 'seed' -> Early-stage Investments")
    print("   - Size $5.01-10M -> 'series a' -> Early-stage Investments")
    print("   - Size > $10M -> 'undisclosed late-stage' -> Late-stage Investments")
    print("   - No size, Age <= 3 -> 'undisclosed early-stage' -> Early-stage Investments")
    print("   - No size, Age > 3 -> 'undisclosed late-stage' -> Late-stage Investments")
    print("   - No size, No age -> 'undisclosed late-stage' -> Late-stage Investments (default)")
    
    return df, both_corporate

def apply_corporate_mapping(df):
    """Apply the Corporate mapping rules to create new columns"""
    
    print("\n7. APPLYING CORPORATE MAPPING RULES")
    print("-" * 50)
    
    # Create new columns for mapped values
    df['Mapped_Type'] = df['Type'].copy()
    df['Mapped_Category'] = df['Category'].copy()
    
    # Convert Date to datetime for year extraction
    df['Transaction_Year'] = pd.to_datetime(df['Date'], format='%d/%m/%Y').dt.year
    
    # Process Corporate transactions
    corporate_mask = (df['Type'] == 'Corporate') | (df['Category'] == 'Corporate')
    corporate_count = 0
    
    for idx in df[corporate_mask].index:
        row = df.loc[idx]
        size = row['Size, $m']
        founded = row['Target Founded']
        trans_year = row['Transaction_Year']
        
        # Determine new type based on rules
        if pd.notna(size) and size > 0:
            if size <= 5.0:
                new_type = 'seed'
                new_category = 'Early-stage Investments'
            elif size <= 10.0:
                new_type = 'series a'
                new_category = 'Early-stage Investments'
            else:
                new_type = 'undisclosed late-stage'
                new_category = 'Late-stage Investments'
        else:
            # No size, check age
            if pd.notna(founded) and founded > 0:
                company_age = trans_year - founded
                if company_age <= 3:
                    new_type = 'undisclosed early-stage'
                    new_category = 'Early-stage Investments'
                else:
                    new_type = 'undisclosed late-stage'
                    new_category = 'Late-stage Investments'
            else:
                # No size, no age - default
                new_type = 'undisclosed late-stage'
                new_category = 'Late-stage Investments'
        
        # Update the mapped columns
        df.at[idx, 'Mapped_Type'] = new_type
        df.at[idx, 'Mapped_Category'] = new_category
        corporate_count += 1
    
    print(f"   Mapped {corporate_count} Corporate transactions")
    
    # Drop the temporary Transaction_Year column
    df = df.drop('Transaction_Year', axis=1)
    
    return df

def map_other_types(df):
    """Map non-Corporate types according to documentation"""
    
    print("\n8. MAPPING OTHER TRANSACTION TYPES")
    print("-" * 50)
    
    # Type mapping dictionary from documentation
    type_mapping = {
        # Early-Stage Types
        'Seed round': ('seed', 'Early-stage Investments'),
        'Grant': ('accelerator / grant', 'Early-stage Investments'),
        'Accelerator/Incubator': ('accelerator / grant', 'Early-stage Investments'),
        'Series A': ('series a', 'Early-stage Investments'),
        'Series A+': ('series a', 'Early-stage Investments'),
        
        # Late-Stage Types
        'Series B': ('series b', 'Late-stage Investments'),
        'Series B+': ('series b', 'Late-stage Investments'),
        'Series C': ('series c', 'Late-stage Investments'),
        'Series D': ('series d', 'Late-stage Investments'),
        'Series D+': ('series d', 'Late-stage Investments'),
        'Series E': ('series e', 'Late-stage Investments'),
        'Series G': ('series e', 'Late-stage Investments'),
        'Series H': ('series e', 'Late-stage Investments'),
        'Growth': ('growth / expansion (not specified)', 'Late-stage Investments'),
        'Fixed Income': ('fixed income', 'Public offering'),
        'Fixed income': ('fixed income', 'Public offering'),
        
        # M&A Types
        'Control': ('m&a control (incl. lbo/mbo)', 'M&A'),
        'Control ': ('m&a control (incl. lbo/mbo)', 'M&A'),  # With trailing space
        'Minority': ('m&a minority', 'M&A'),
        
        # Public Offering Types
        'IPO': ('listing (ipo/spac)', 'Public offering'),
        'SPAC': ('listing (ipo/spac)', 'Public offering'),
        'Direct Listing': ('listing (ipo/spac)', 'Public offering'),
        'PIPE': ('pipe', 'Public offering'),
        'PIPE, Other': ('pipe', 'Public offering'),
        'PIPE, other': ('pipe', 'Public offering'),
        
        # Generic/Undefined
        'Undisclosed': ('undisclosed early-stage', 'Early-stage Investments'),
        'Late-stage': ('undisclosed late-stage', 'Late-stage Investments'),
    }
    
    non_corporate_mask = ~((df['Type'] == 'Corporate') | (df['Category'] == 'Corporate'))
    mapped_count = 0
    
    for idx in df[non_corporate_mask].index:
        original_type = df.at[idx, 'Type']
        original_category = df.at[idx, 'Category']
        
        # Check if type exists in mapping
        if original_type in type_mapping:
            new_type, new_category = type_mapping[original_type]
            df.at[idx, 'Mapped_Type'] = new_type
            
            # M&A category override rule
            if original_category != 'M&A':
                df.at[idx, 'Mapped_Category'] = new_category
            # If original category is M&A, keep it
            
            mapped_count += 1
    
    print(f"   Mapped {mapped_count} non-Corporate transactions")
    
    return df

def generate_summary(df):
    """Generate summary statistics"""
    
    print("\n9. FINAL MAPPING SUMMARY")
    print("=" * 70)
    
    # Count changes
    type_changed = (df['Type'] != df['Mapped_Type']).sum()
    category_changed = (df['Category'] != df['Mapped_Category']).sum()
    
    print(f"   Total records: {len(df)}")
    print(f"   Types changed: {type_changed}")
    print(f"   Categories changed: {category_changed}")
    
    print("\n   ORIGINAL CATEGORY DISTRIBUTION:")
    for cat, count in df['Category'].value_counts().items():
        print(f"   - {cat}: {count}")
    
    print("\n   MAPPED CATEGORY DISTRIBUTION:")
    for cat, count in df['Mapped_Category'].value_counts().items():
        print(f"   - {cat}: {count}")
    
    print("\n   ORIGINAL TYPE DISTRIBUTION (Top 10):")
    for typ, count in df['Type'].value_counts().head(10).items():
        print(f"   - {typ}: {count}")
    
    print("\n   MAPPED TYPE DISTRIBUTION (Top 10):")
    for typ, count in df['Mapped_Type'].value_counts().head(10).items():
        print(f"   - {typ}: {count}")

def main():
    """Main execution function"""
    
    # Analyze Corporate transactions
    df, corporate_df = analyze_corporate_transactions()
    
    # Apply Corporate mapping
    df = apply_corporate_mapping(df)
    
    # Map other types
    df = map_other_types(df)
    
    # Generate summary
    generate_summary(df)
    
    # Save cleaned file
    output_file = Path('../output/ig_arc_unmapped_cleaned.csv')
    print(f"\n10. SAVING CLEANED FILE")
    print("-" * 50)
    print(f"   Output file: {output_file}")
    df.to_csv(output_file, index=False, encoding='utf-8')
    print("   File saved successfully!")
    
    # Create audit report
    audit_file = Path('../output/corporate_mapping_audit.txt')
    with open(audit_file, 'w', encoding='utf-8') as f:
        f.write("CORPORATE MAPPING AUDIT REPORT\n")
        f.write("=" * 70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Input file: ig_arc_unmapped.csv\n")
        f.write(f"Output file: ig_arc_unmapped_cleaned.csv\n\n")
        
        # Corporate transactions details
        corp_mask = (df['Type'] == 'Corporate') | (df['Category'] == 'Corporate')
        corp_df = df[corp_mask][['IG_ID', 'Target name', 'Type', 'Category', 'Size, $m', 
                                  'Target Founded', 'Mapped_Type', 'Mapped_Category']]
        
        f.write("CORPORATE TRANSACTIONS MAPPED:\n")
        f.write("-" * 70 + "\n")
        f.write(corp_df.to_string())
        
    print(f"\n   Audit report saved: {audit_file}")
    
    print("\n" + "=" * 70)
    print("MAPPING COMPLETE!")
    print("=" * 70)

if __name__ == "__main__":
    main()