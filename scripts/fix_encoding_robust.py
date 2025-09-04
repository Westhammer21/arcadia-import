#!/usr/bin/env python3
"""
Robust encoding fix for all text columns
Created: 2025-09-03
Purpose: Fix encoding issues while preserving legitimate apostrophes
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import unicodedata

def fix_text_encoding(text):
    """Fix encoding issues while preserving legitimate apostrophes"""
    if pd.isna(text) or text == '':
        return text
    
    text = str(text)
    
    # First pass: Fix common UTF-8 encoding issues that show up as garbled text
    # These are the actual patterns you're seeing in the data
    common_fixes = {
        'â€™': "'",  # Right single quotation mark
        'â€˜': "'",  # Left single quotation mark  
        'â€œ': '"',  # Left double quotation mark
        'â€': '"',   # Right double quotation mark
        'â€"': '-',  # Em dash
        'â€"': '-',  # En dash
        'Ã¢': 'a',
        'Ã©': 'e',
        'Ã¼': 'u',
        'Ã¶': 'o',
        'Ã§': 'c',
        'Ã±': 'n',
        'Ã¡': 'a',
        'Ã³': 'o',
        'Ã': 'A',
        'Â': '',  # Common garbage character
    }
    
    for old, new in common_fixes.items():
        text = text.replace(old, new)
    
    # Second pass: Clean up remaining non-ASCII while preserving valid apostrophes
    result = []
    for char in text:
        if ord(char) < 128:  # Standard ASCII
            result.append(char)
        elif char in ["'", "'"]:  # Preserve various apostrophe forms
            result.append("'")
        elif ord(char) == 160:  # Non-breaking space
            result.append(' ')
        else:
            # Try to get ASCII equivalent
            try:
                ascii_char = unicodedata.normalize('NFKD', char).encode('ascii', 'ignore').decode('ascii')
                if ascii_char:
                    result.append(ascii_char)
            except:
                pass  # Skip character if can't convert
    
    text = ''.join(result)
    
    # Clean up multiple spaces
    text = ' '.join(text.split())
    
    return text

def main():
    """Main execution function"""
    
    print("=" * 70)
    print("ROBUST ENCODING FIX FOR ALL TEXT COLUMNS")
    print("=" * 70)
    
    # File paths
    input_file = Path('../output/ig_arc_unmapped_FINAL_COMPLETE.csv')
    backup_file = Path(f'../output/ig_arc_unmapped_FINAL_COMPLETE_BACKUP_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    output_file = Path('../output/ig_arc_unmapped_FINAL_COMPLETE.csv')
    
    # Load data
    print("\n1. Loading data")
    print("-" * 50)
    print(f"   Input: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8', dtype=str)  # Read all as string to avoid issues
    print(f"   Loaded {len(df)} records with {len(df.columns)} columns")
    
    # Create backup
    print(f"   Creating backup: {backup_file}")
    df.to_csv(backup_file, index=False, encoding='utf-8')
    
    # Identify text columns to fix
    text_columns = ['Target name', 'Investors / Buyers', 'Short description']
    
    # Track changes
    total_changes = 0
    examples = []
    
    print("\n2. Processing text columns")
    print("-" * 50)
    
    for col in text_columns:
        if col in df.columns:
            print(f"\n   Processing: {col}")
            col_changes = 0
            
            # Apply fix to each value
            for idx in range(len(df)):
                original = df.at[idx, col]
                if pd.notna(original) and original != '':
                    fixed = fix_text_encoding(original)
                    if fixed != original:
                        df.at[idx, col] = fixed
                        col_changes += 1
                        total_changes += 1
                        
                        # Store first 3 examples per column
                        if col_changes <= 3:
                            examples.append({
                                'column': col,
                                'row': idx + 2,
                                'original': original[:40] if len(original) > 40 else original,
                                'fixed': fixed[:40] if len(fixed) > 40 else fixed
                            })
            
            print(f"     Fixed {col_changes} values")
    
    # Save fixed file
    print("\n3. Saving fixed file")
    print("-" * 50)
    print(f"   Output: {output_file}")
    df.to_csv(output_file, index=False, encoding='utf-8')
    print("   File saved successfully!")
    
    # Show examples
    if examples:
        print("\n4. Sample fixes")
        print("-" * 50)
        for ex in examples[:10]:
            print(f"   {ex['column']} (Row {ex['row']}):")
            print(f"     Before: {ex['original']}")
            print(f"     After:  {ex['fixed']}")
    
    # Check specific problematic entries
    print("\n5. Checking known problematic names")
    print("-" * 50)
    
    # Look for entries with encoding issues
    problematic_patterns = ["â€™", "â€˜", "â€œ", "â€", "Ã"]
    
    for col in text_columns:
        if col in df.columns:
            issues_found = 0
            for pattern in problematic_patterns:
                mask = df[col].astype(str).str.contains(pattern, case=False, na=False, regex=False)
                issues_found += mask.sum()
            
            if issues_found > 0:
                print(f"   WARNING: {col} still has {issues_found} potential encoding issues")
            else:
                print(f"   OK: {col} appears clean")
    
    # Final summary
    print("\n" + "=" * 70)
    print("ENCODING FIX COMPLETE!")
    print("=" * 70)
    print(f"\nResults:")
    print(f"  Total values fixed: {total_changes}")
    print(f"\nFiles:")
    print(f"  Fixed data: {output_file}")
    print(f"  Backup: {backup_file}")
    
    # Create simple report
    report_file = Path('../output/encoding_fix_report_final.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"Encoding Fix Report\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Total fixes: {total_changes}\n\n")
        
        f.write("Sample fixes:\n")
        for ex in examples[:20]:
            f.write(f"{ex['column']} Row {ex['row']}: '{ex['original']}' -> '{ex['fixed']}'\n")
    
    print(f"  Report: {report_file}")

if __name__ == "__main__":
    main()