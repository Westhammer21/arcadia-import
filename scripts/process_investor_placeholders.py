#!/usr/bin/env python3
"""
Script to detect and standardize placeholder values in Investors/Buyers column
Created: 2025-09-03
Purpose: Convert placeholder patterns (dashes, short strings, undisclosed variations) to "Undisclosed"
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import re

def analyze_investor_patterns(df):
    """Analyze the Investors/Buyers column for placeholder patterns"""
    
    print("\n2. Analyzing Investors/Buyers column patterns")
    print("-" * 50)
    
    column = 'Investors / Buyers'
    
    # Initialize pattern counters
    patterns = {
        'empty_null': [],
        'dash_pattern': [],
        'short_string': [],
        'undisclosed_variation': [],
        'valid_investor': []
    }
    
    # Pattern definitions
    dash_regex = re.compile(r'^-+$')  # One or more dashes only
    undisclosed_regex = re.compile(r'^(undisclosed|not\s*disclosed|n/?a|none|unknown|tbd|tba)$', re.IGNORECASE)
    
    for idx, row in df.iterrows():
        value = row[column]
        row_num = idx + 2  # Excel row number
        
        # Check for empty/null
        if pd.isna(value) or value == '' or value is None:
            patterns['empty_null'].append({
                'row': row_num,
                'IG_ID': row['IG_ID'],
                'original': value,
                'pattern': 'Empty/Null'
            })
        else:
            value_str = str(value).strip()
            
            # Check for dash pattern
            if dash_regex.match(value_str):
                patterns['dash_pattern'].append({
                    'row': row_num,
                    'IG_ID': row['IG_ID'],
                    'original': value,
                    'pattern': 'Dash(es)'
                })
            # Check for short string (≤2 chars after stripping)
            elif len(value_str) <= 2:
                patterns['short_string'].append({
                    'row': row_num,
                    'IG_ID': row['IG_ID'],
                    'original': value,
                    'pattern': f'Short string ({len(value_str)} char)'
                })
            # Check for undisclosed variations
            elif undisclosed_regex.match(value_str):
                patterns['undisclosed_variation'].append({
                    'row': row_num,
                    'IG_ID': row['IG_ID'],
                    'original': value,
                    'pattern': 'Undisclosed variation'
                })
            else:
                # Valid investor name
                patterns['valid_investor'].append({
                    'row': row_num,
                    'IG_ID': row['IG_ID'],
                    'original': value,
                    'pattern': 'Valid investor'
                })
    
    # Print summary
    print(f"   Total records analyzed: {len(df)}")
    print(f"   Empty/Null values: {len(patterns['empty_null'])}")
    print(f"   Dash patterns: {len(patterns['dash_pattern'])}")
    print(f"   Short strings (<=2 chars): {len(patterns['short_string'])}")
    print(f"   Undisclosed variations: {len(patterns['undisclosed_variation'])}")
    print(f"   Valid investor names: {len(patterns['valid_investor'])}")
    
    total_placeholders = (len(patterns['empty_null']) + 
                         len(patterns['dash_pattern']) + 
                         len(patterns['short_string']) + 
                         len(patterns['undisclosed_variation']))
    
    print(f"\n   Total placeholders to convert: {total_placeholders} ({total_placeholders/len(df)*100:.1f}%)")
    
    return patterns

def apply_placeholder_conversion(df, patterns):
    """Apply conversion of placeholders to 'Undisclosed'"""
    
    print("\n3. Applying placeholder conversions")
    print("-" * 50)
    
    column = 'Investors / Buyers'
    
    # Create a copy for processing
    df_processed = df.copy()
    
    # Track conversions
    conversions = []
    
    # Convert all placeholder patterns to "Undisclosed"
    for pattern_type in ['empty_null', 'dash_pattern', 'short_string', 'undisclosed_variation']:
        for item in patterns[pattern_type]:
            row_idx = item['row'] - 2  # Convert back to DataFrame index
            original = df_processed.at[row_idx, column]
            
            # Apply conversion
            df_processed.at[row_idx, column] = 'Undisclosed'
            
            conversions.append({
                'row': item['row'],
                'IG_ID': item['IG_ID'],
                'original': original,
                'converted': 'Undisclosed',
                'pattern_type': pattern_type
            })
    
    print(f"   Converted {len(conversions)} placeholder values to 'Undisclosed'")
    
    # Show examples of conversions
    if conversions:
        print("\n   Sample conversions:")
        unique_originals = {}
        for conv in conversions[:20]:  # Show up to 20 unique patterns
            orig = str(conv['original']) if conv['original'] is not None else 'None'
            if orig not in unique_originals:
                unique_originals[orig] = conv['pattern_type']
                print(f"     '{orig}' -> 'Undisclosed' ({conv['pattern_type']})")
            if len(unique_originals) >= 10:
                break
    
    return df_processed, conversions

def create_detailed_report(patterns, conversions, output_dir):
    """Create detailed report of investor placeholder processing"""
    
    report_file = output_dir / 'INVESTOR_PLACEHOLDER_REPORT.md'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Investor Placeholder Processing Report\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Script**: process_investor_placeholders.py\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"Analyzed and standardized placeholder values in the 'Investors / Buyers' column ")
        f.write(f"across 883 unmapped transactions.\n\n")
        
        total_placeholders = len(conversions)
        f.write(f"- **Total records processed**: 883\n")
        f.write(f"- **Placeholders detected**: {total_placeholders}\n")
        f.write(f"- **Conversion rate**: {total_placeholders/883*100:.1f}%\n")
        f.write(f"- **Valid investor names preserved**: {len(patterns['valid_investor'])}\n\n")
        
        f.write("---\n\n")
        
        f.write("## Pattern Detection Results\n\n")
        f.write("### Detection Rules Applied:\n")
        f.write("1. **Empty/Null**: Empty strings, null values, or missing data\n")
        f.write("2. **Dash Pattern**: One or more dashes only (-, --, ---, etc.)\n")
        f.write("3. **Short String**: Strings with <=2 characters after trimming\n")
        f.write("4. **Undisclosed Variations**: Case-insensitive matches for 'undisclosed', 'n/a', 'none', etc.\n\n")
        
        f.write("### Pattern Distribution:\n\n")
        f.write("| Pattern Type | Count | Percentage | Examples |\n")
        f.write("|--------------|-------|------------|----------|\n")
        f.write(f"| Empty/Null | {len(patterns['empty_null'])} | "
               f"{len(patterns['empty_null'])/883*100:.1f}% | (empty), None, null |\n")
        f.write(f"| Dash Pattern | {len(patterns['dash_pattern'])} | "
               f"{len(patterns['dash_pattern'])/883*100:.1f}% | -, --, --- |\n")
        f.write(f"| Short String | {len(patterns['short_string'])} | "
               f"{len(patterns['short_string'])/883*100:.1f}% | NA, ., ?, XX |\n")
        f.write(f"| Undisclosed Variation | {len(patterns['undisclosed_variation'])} | "
               f"{len(patterns['undisclosed_variation'])/883*100:.1f}% | undisclosed, N/A, TBD |\n")
        f.write(f"| **Total Placeholders** | **{total_placeholders}** | "
               f"**{total_placeholders/883*100:.1f}%** | - |\n")
        f.write(f"| Valid Investors | {len(patterns['valid_investor'])} | "
               f"{len(patterns['valid_investor'])/883*100:.1f}% | Actual investor names |\n\n")
        
        f.write("---\n\n")
        
        f.write("## Conversion Examples\n\n")
        f.write("### Unique Patterns Converted:\n\n")
        
        # Group conversions by original value
        unique_conversions = {}
        for conv in conversions:
            orig = str(conv['original']) if conv['original'] is not None else 'None'
            if orig not in unique_conversions:
                unique_conversions[orig] = {
                    'count': 0,
                    'pattern_type': conv['pattern_type'],
                    'examples': []
                }
            unique_conversions[orig]['count'] += 1
            if len(unique_conversions[orig]['examples']) < 3:
                unique_conversions[orig]['examples'].append(conv['IG_ID'])
        
        # Sort by count
        sorted_patterns = sorted(unique_conversions.items(), key=lambda x: x[1]['count'], reverse=True)
        
        f.write("| Original Value | Pattern Type | Occurrences | Sample IG_IDs |\n")
        f.write("|----------------|--------------|-------------|---------------|\n")
        
        for orig, info in sorted_patterns[:20]:  # Show top 20
            orig_display = f"'{orig}'" if orig != 'None' else '(empty)'
            examples = ', '.join(str(e) for e in info['examples'])
            f.write(f"| {orig_display} | {info['pattern_type'].replace('_', ' ').title()} | "
                   f"{info['count']} | {examples} |\n")
        
        if len(sorted_patterns) > 20:
            f.write(f"\n*... and {len(sorted_patterns)-20} more unique patterns*\n")
        
        f.write("\n---\n\n")
        
        f.write("## Records with Placeholders\n\n")
        f.write("### First 50 Converted Records:\n\n")
        
        f.write("| Row | IG_ID | Target Name | Original Investor | Pattern |\n")
        f.write("|-----|-------|-------------|-------------------|----------|\n")
        
        # Get target names for context
        df_temp = pd.read_csv('../output/ig_arc_unmapped_final.csv', encoding='utf-8')
        
        for conv in conversions[:50]:
            row_idx = conv['row'] - 2
            if row_idx < len(df_temp):
                target = df_temp.at[row_idx, 'Target name']
                orig_display = str(conv['original']) if conv['original'] is not None else '(empty)'
                f.write(f"| {conv['row']} | {conv['IG_ID']} | {target[:30]}... | "
                       f"{orig_display[:20]}... | {conv['pattern_type'].replace('_', ' ')} |\n")
        
        if len(conversions) > 50:
            f.write(f"\n*... and {len(conversions)-50} more converted records*\n")
        
        f.write("\n---\n\n")
        
        f.write("## Data Quality Improvement\n\n")
        f.write("### Before Processing:\n")
        f.write(f"- Inconsistent placeholder representations: {len(unique_conversions)} unique patterns\n")
        f.write(f"- Mix of empty values, dashes, and text variations\n")
        f.write(f"- Difficult to analyze investor participation rates\n\n")
        
        f.write("### After Processing:\n")
        f.write(f"- Standardized placeholder: 'Undisclosed' for all unknown investors\n")
        f.write(f"- Clean distinction between known ({len(patterns['valid_investor'])}) "
               f"and unknown ({total_placeholders}) investors\n")
        f.write(f"- Improved data consistency for analysis and reporting\n\n")
        
        f.write("---\n\n")
        f.write("**Status**: Complete\n")
        f.write(f"**Output File**: ig_arc_unmapped_investors_cleaned.csv\n")
    
    print(f"\n   Report saved: {report_file}")
    
    return report_file

def main():
    """Main execution function"""
    
    print("=" * 70)
    print("INVESTOR PLACEHOLDER STANDARDIZATION")
    print("=" * 70)
    
    # File paths
    input_file = Path('../output/ig_arc_unmapped_final.csv')
    backup_file = Path(f'../output/ig_arc_unmapped_final_BACKUP_INVESTORS_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    output_file = Path('../output/ig_arc_unmapped_investors_cleaned.csv')
    output_dir = Path('../output')
    
    # Load data
    print("\n1. Loading unmapped transactions file")
    print("-" * 50)
    print(f"   Input file: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"   Loaded {len(df)} records")
    
    # Create backup
    print(f"   Creating backup: {backup_file}")
    df.to_csv(backup_file, index=False, encoding='utf-8')
    
    # Analyze patterns
    patterns = analyze_investor_patterns(df)
    
    # Apply conversions
    df_processed, conversions = apply_placeholder_conversion(df, patterns)
    
    # Save processed file
    print("\n4. Saving processed file")
    print("-" * 50)
    print(f"   Output file: {output_file}")
    df_processed.to_csv(output_file, index=False, encoding='utf-8')
    print("   File saved successfully!")
    
    # Create detailed report
    print("\n5. Creating detailed report")
    print("-" * 50)
    report_file = create_detailed_report(patterns, conversions, output_dir)
    
    # Save conversion details as CSV for reference
    if conversions:
        conversions_file = output_dir / 'investor_placeholder_conversions.csv'
        pd.DataFrame(conversions).to_csv(conversions_file, index=False, encoding='utf-8')
        print(f"   Conversion details saved: {conversions_file}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("PROCESSING COMPLETE!")
    print("=" * 70)
    print(f"\nResults:")
    print(f"  Total records: {len(df)}")
    print(f"  Placeholders converted: {len(conversions)} ({len(conversions)/len(df)*100:.1f}%)")
    print(f"  Valid investors preserved: {len(patterns['valid_investor'])} ({len(patterns['valid_investor'])/len(df)*100:.1f}%)")
    print(f"\nOutput files:")
    print(f"  - Processed data: {output_file}")
    print(f"  - Processing report: {report_file}")
    print(f"  - Backup file: {backup_file}")
    
    return {
        'total_records': len(df),
        'placeholders_converted': len(conversions),
        'valid_investors': len(patterns['valid_investor']),
        'conversion_rate': len(conversions)/len(df)*100
    }

if __name__ == "__main__":
    results = main()