#!/usr/bin/env python3
"""
Final comprehensive encoding fix for all text columns
Created: 2025-09-03
Purpose: Fix ALL encoding issues while preserving legitimate apostrophes
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import re

def fix_encoding_comprehensive(text):
    """Fix all encoding issues in text while preserving legitimate apostrophes"""
    if pd.isna(text) or text == '':
        return text
    
    text = str(text)
    
    # Dictionary of replacements
    replacements = {
        # Smart quotes and apostrophes (but preserve regular apostrophes)
        'â€™': "'",  # Right single quotation mark
        'â€˜': "'",  # Left single quotation mark
        'â€œ': '"',  # Left double quotation mark
        'â€': '"',   # Right double quotation mark
        'â€"': '-',  # Em dash
        'â€"': '-',  # En dash
        'â€¦': '...',  # Ellipsis
        'â€¢': '*',  # Bullet
        
        # Spaces
        'â€‚': ' ',  # En space
        'â€ƒ': ' ',  # Em space
        'â€‰': ' ',  # Thin space
        'â€Š': ' ',  # Hair space
        'â€‹': '',   # Zero width space
        
        # Currency
        'â‚¬': 'EUR',  # Euro
        'Â£': 'GBP',   # Pound
        'Â¥': 'JPY',   # Yen
        'â‚¹': 'INR',   # Rupee
        
        # Symbols
        'Â©': '(c)',   # Copyright
        'Â®': '(R)',   # Registered
        'â„¢': '(TM)',  # Trademark
        'Â°': ' deg',  # Degree
        
        # Math
        'Ã—': 'x',     # Multiplication
        'Ã·': '/',     # Division
        'Â±': '+/-',   # Plus-minus
        'âˆž': 'inf',   # Infinity
        
        # Fractions
        'Â½': '1/2',
        'Â¼': '1/4',
        'Â¾': '3/4',
        
        # Accented characters - A
        'Ã¡': 'a', 'Ã ': 'a', 'Ã¢': 'a', 'Ã¤': 'a', 'Ã£': 'a', 'Ã¥': 'a',
        'Ã': 'A', 'Ã€': 'A', 'Ã‚': 'A', 'Ã„': 'A', 'Ãƒ': 'A', 'Ã…': 'A',
        
        # E
        'Ã©': 'e', 'Ã¨': 'e', 'Ãª': 'e', 'Ã«': 'e',
        'Ã‰': 'E', 'Ãˆ': 'E', 'ÃŠ': 'E', 'Ã‹': 'E',
        
        # I
        'Ã­': 'i', 'Ã¬': 'i', 'Ã®': 'i', 'Ã¯': 'i',
        'Ã': 'I', 'ÃŒ': 'I', 'ÃŽ': 'I', 'Ã': 'I',
        
        # O
        'Ã³': 'o', 'Ã²': 'o', 'Ã´': 'o', 'Ã¶': 'o', 'Ãµ': 'o', 'Ã¸': 'o',
        'Ã"': 'O', 'Ã'': 'O', 'Ã"': 'O', 'Ã–': 'O', 'Ã•': 'O', 'Ã˜': 'O',
        
        # U
        'Ãº': 'u', 'Ã¹': 'u', 'Ã»': 'u', 'Ã¼': 'u',
        'Ãš': 'U', 'Ã™': 'U', 'Ã›': 'U', 'Ãœ': 'U',
        
        # Other
        'Ã±': 'n', 'Ã'': 'N',
        'Ã§': 'c', 'Ã‡': 'C',
        'ÃŸ': 'ss',
        'Ã¿': 'y',
        'Ã¦': 'ae', 'Ã†': 'AE',
        
        # HTML entities
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&apos;': "'",
        '&nbsp;': ' ',
    }
    
    # Apply all replacements
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Clean up any remaining non-ASCII characters (but preserve regular apostrophes)
    result = []
    for char in text:
        if ord(char) < 128:  # ASCII
            result.append(char)
        elif char == "'":  # Preserve apostrophe
            result.append(char)
        elif ord(char) == 160:  # Non-breaking space
            result.append(' ')
        # Skip other non-ASCII characters
    
    text = ''.join(result)
    
    # Clean up multiple spaces
    text = ' '.join(text.split())
    
    return text

def main():
    """Main execution function"""
    
    print("=" * 70)
    print("COMPREHENSIVE ENCODING FIX FOR ALL TEXT COLUMNS")
    print("=" * 70)
    
    # File paths
    input_file = Path('../output/ig_arc_unmapped_FINAL_COMPLETE.csv')
    backup_file = Path(f'../output/ig_arc_unmapped_FINAL_COMPLETE_BACKUP_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    output_file = Path('../output/ig_arc_unmapped_FINAL_COMPLETE.csv')
    
    # Load data
    print("\n1. Loading data")
    print("-" * 50)
    print(f"   Input: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"   Loaded {len(df)} records with {len(df.columns)} columns")
    
    # Create backup
    print(f"   Creating backup: {backup_file}")
    df.to_csv(backup_file, index=False, encoding='utf-8')
    
    # Identify text columns to fix
    text_columns = ['Target name', 'Investors / Buyers', 'Short description']
    
    # Track changes
    changes = {col: {'total': 0, 'examples': []} for col in text_columns}
    
    print("\n2. Processing text columns")
    print("-" * 50)
    
    for col in text_columns:
        if col in df.columns:
            print(f"\n   Processing: {col}")
            
            # Apply fix to each value
            for idx in range(len(df)):
                original = df.at[idx, col]
                if pd.notna(original) and original != '':
                    fixed = fix_encoding_comprehensive(original)
                    if fixed != original:
                        df.at[idx, col] = fixed
                        changes[col]['total'] += 1
                        
                        # Store examples (first 5)
                        if len(changes[col]['examples']) < 5:
                            changes[col]['examples'].append({
                                'row': idx + 2,
                                'original': str(original)[:50] + '...' if len(str(original)) > 50 else str(original),
                                'fixed': fixed[:50] + '...' if len(fixed) > 50 else fixed
                            })
            
            print(f"     Fixed {changes[col]['total']} values")
            
            # Show examples
            if changes[col]['examples']:
                print(f"     Examples:")
                for ex in changes[col]['examples'][:3]:
                    orig_display = ex['original'].encode('ascii', 'replace').decode('ascii')
                    fixed_display = ex['fixed']
                    print(f"       Row {ex['row']}: '{orig_display}' -> '{fixed_display}'")
    
    # Save fixed file
    print("\n3. Saving fixed file")
    print("-" * 50)
    print(f"   Output: {output_file}")
    df.to_csv(output_file, index=False, encoding='utf-8')
    print("   File saved successfully!")
    
    # Generate report
    print("\n4. Creating encoding fix report")
    print("-" * 50)
    
    report_file = Path('../output/encoding_fix_final_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("COMPREHENSIVE ENCODING FIX REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("SUMMARY\n")
        f.write("-" * 30 + "\n")
        total_fixed = sum(changes[col]['total'] for col in text_columns)
        f.write(f"Total values fixed: {total_fixed}\n\n")
        
        for col in text_columns:
            if col in df.columns:
                f.write(f"\n{col}:\n")
                f.write(f"  Fixed: {changes[col]['total']} values\n")
                if changes[col]['examples']:
                    f.write("  Examples:\n")
                    for ex in changes[col]['examples']:
                        # Safely display the examples
                        orig_safe = ex['original'].encode('ascii', 'replace').decode('ascii')
                        f.write(f"    Row {ex['row']}: '{orig_safe}' -> '{ex['fixed']}'\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("All encoding issues have been fixed while preserving legitimate apostrophes.\n")
    
    print(f"   Report saved: {report_file}")
    
    # Verify specific problematic names are fixed
    print("\n5. Verifying known problematic names")
    print("-" * 50)
    problematic_names = [
        "We're Five Games",  # Should keep apostrophe
        "That's No Moon Entertainment",  # Should keep apostrophe
        "Bhooshans Junior"  # Should fix encoding
    ]
    
    for name in problematic_names:
        matches = df[df['Target name'].str.contains(name.split()[0], case=False, na=False)]
        if not matches.empty:
            fixed_name = matches.iloc[0]['Target name']
            print(f"   '{name}' -> '{fixed_name}'")
    
    # Final summary
    print("\n" + "=" * 70)
    print("ENCODING FIX COMPLETE!")
    print("=" * 70)
    print(f"\nResults:")
    for col in text_columns:
        if col in df.columns:
            print(f"  {col}: {changes[col]['total']} values fixed")
    print(f"\nFiles:")
    print(f"  Fixed data: {output_file}")
    print(f"  Backup: {backup_file}")
    print(f"  Report: {report_file}")

if __name__ == "__main__":
    main()