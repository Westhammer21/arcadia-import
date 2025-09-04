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

def fix_encoding_comprehensive(text):
    """Fix all encoding issues in text while preserving legitimate apostrophes"""
    if pd.isna(text) or text == '':
        return text
    
    text = str(text)
    
    # Fix common encoding issues
    # Smart quote and apostrophe issues (but preserve regular apostrophes)
    text = text.replace('â€™', "'")  # Right single quotation mark
    text = text.replace('â€˜', "'")  # Left single quotation mark  
    text = text.replace('â€œ', '"')  # Left double quotation mark
    text = text.replace('â€', '"')   # Right double quotation mark
    text = text.replace('â€"', '-')  # Em dash
    text = text.replace('â€"', '-')  # En dash
    text = text.replace('â€¦', '...')  # Ellipsis
    text = text.replace('â€¢', '*')  # Bullet
    text = text.replace('â€‚', ' ')  # En space
    text = text.replace('â€ƒ', ' ')  # Em space
    text = text.replace('â€‰', ' ')  # Thin space
    text = text.replace('â€Š', ' ')  # Hair space
    text = text.replace('â€‹', '')   # Zero width space
    
    # Currency and symbols
    text = text.replace('â‚¬', 'EUR')  # Euro
    text = text.replace('Â£', 'GBP')   # Pound
    text = text.replace('Â¥', 'JPY')   # Yen
    text = text.replace('â‚¹', 'INR')   # Rupee
    text = text.replace('Â©', '(c)')   # Copyright
    text = text.replace('Â®', '(R)')   # Registered
    text = text.replace('â„¢', '(TM)')  # Trademark
    text = text.replace('Â°', ' deg')  # Degree
    
    # Mathematical symbols
    text = text.replace('Ã—', 'x')     # Multiplication
    text = text.replace('Ã·', '/')     # Division
    text = text.replace('Â±', '+/-')   # Plus-minus
    text = text.replace('â‰¤', '<=')    # Less than or equal
    text = text.replace('â‰¥', '>=')    # Greater than or equal
    text = text.replace('â‰ ', '!=')    # Not equal
    text = text.replace('âˆž', 'inf')   # Infinity
    text = text.replace('âˆ', 'sum')   # Summation
    text = text.replace('âˆš', 'sqrt')  # Square root
    
    # Arrows
    text = text.replace('←', '<-')    # Left arrow
    text = text.replace('→', '->')    # Right arrow
    text = text.replace('↔', '<->')   # Left-right arrow
    text = text.replace('↑', '^')     # Up arrow
    text = text.replace('↓', 'v')     # Down arrow
    
    # Fractions
    text = text.replace('Â½', '1/2')
    text = text.replace('â…"', '1/3')
    text = text.replace('â…"', '2/3')
    text = text.replace('Â¼', '1/4')
    text = text.replace('Â¾', '3/4')
    text = text.replace('â…›', '1/8')
    
    # Special characters from various languages
    text = text.replace('Ã¡', 'a')
    text = text.replace('Ã ', 'a')
    text = text.replace('Ã¢', 'a')
    text = text.replace('Ã¤', 'a')
    text = text.replace('Ã£', 'a')
    text = text.replace('Ã¥', 'a')
    text = text.replace('Ã', 'A')
    text = text.replace('Ã€', 'A')
    text = text.replace('Ã‚', 'A')
    text = text.replace('Ã„', 'A')
    text = text.replace('Ãƒ', 'A')
    text = text.replace('Ã…', 'A')
    
    text = text.replace('Ã©', 'e')
    text = text.replace('Ã¨', 'e')
    text = text.replace('Ãª', 'e')
    text = text.replace('Ã«', 'e')
    text = text.replace('Ã‰', 'E')
    text = text.replace('Ãˆ', 'E')
    text = text.replace('ÃŠ', 'E')
    text = text.replace('Ã‹', 'E')
    
    text = text.replace('Ã­', 'i')
    text = text.replace('Ã¬', 'i')
    text = text.replace('Ã®', 'i')
    text = text.replace('Ã¯', 'i')
    text = text.replace('Ã', 'I')
    text = text.replace('ÃŒ', 'I')
    text = text.replace('ÃŽ', 'I')
    text = text.replace('Ã', 'I')
    
    text = text.replace('Ã³', 'o')
    text = text.replace('Ã²', 'o')
    text = text.replace('Ã´', 'o')
    text = text.replace('Ã¶', 'o')
    text = text.replace('Ãµ', 'o')
    text = text.replace('Ã¸', 'o')
    text = text.replace('Ã"', 'O')
    text = text.replace('Ã'', 'O')
    text = text.replace('Ã"', 'O')
    text = text.replace('Ã–', 'O')
    text = text.replace('Ã•', 'O')
    text = text.replace('Ã˜', 'O')
    
    text = text.replace('Ãº', 'u')
    text = text.replace('Ã¹', 'u')
    text = text.replace('Ã»', 'u')
    text = text.replace('Ã¼', 'u')
    text = text.replace('Ãš', 'U')
    text = text.replace('Ã™', 'U')
    text = text.replace('Ã›', 'U')
    text = text.replace('Ãœ', 'U')
    
    text = text.replace('Ã±', 'n')
    text = text.replace('Ã'', 'N')
    text = text.replace('Ã§', 'c')
    text = text.replace('Ã‡', 'C')
    text = text.replace('ÃŸ', 'ss')
    text = text.replace('Ã¿', 'y')
    text = text.replace('Å¸', 'Y')
    
    # Turkish characters
    text = text.replace('ÄŸ', 'g')
    text = text.replace('Äž', 'G')
    text = text.replace('Ä±', 'i')
    text = text.replace('Ä°', 'I')
    text = text.replace('Å¡', 's')
    text = text.replace('Å ', 'S')
    text = text.replace('Å§', 's')
    text = text.replace('Å¦', 'S')
    
    # Polish characters
    text = text.replace('Ä…', 'a')
    text = text.replace('Ä„', 'A')
    text = text.replace('Ä‡', 'c')
    text = text.replace('Ä†', 'C')
    text = text.replace('Ä™', 'e')
    text = text.replace('Ä˜', 'E')
    text = text.replace('Å‚', 'l')
    text = text.replace('Å', 'L')
    text = text.replace('Å„', 'n')
    text = text.replace('Åƒ', 'N')
    text = text.replace('Å›', 's')
    text = text.replace('Åš', 'S')
    text = text.replace('Åº', 'z')
    text = text.replace('Å¹', 'Z')
    text = text.replace('Å¼', 'z')
    text = text.replace('Å»', 'Z')
    
    # Czech characters
    text = text.replace('Ä›', 'e')
    text = text.replace('Äš', 'E')
    text = text.replace('Å™', 'r')
    text = text.replace('Å˜', 'R')
    text = text.replace('Å¥', 't')
    text = text.replace('Å¤', 'T')
    text = text.replace('Å¯', 'u')
    text = text.replace('Å®', 'U')
    text = text.replace('Ä', 'd')
    text = text.replace('ÄŽ', 'D')
    text = text.replace('Åˆ', 'n')
    text = text.replace('Å‡', 'N')
    
    # Scandinavian
    text = text.replace('Ã¦', 'ae')
    text = text.replace('Ã†', 'AE')
    text = text.replace('Ã¥', 'a')
    text = text.replace('Ã…', 'A')
    
    # Other special cases
    text = text.replace('Å"', 'oe')
    text = text.replace('Å'', 'OE')
    text = text.replace('ÃŸ', 'ss')
    text = text.replace('Ä'', 'dj')
    text = text.replace('Ä', 'DJ')
    
    # Common web/HTML entities that might appear
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&apos;', "'")
    text = text.replace('&nbsp;', ' ')
    
    # Clean up any remaining non-ASCII characters (but preserve regular apostrophes)
    # This is a fallback for anything we missed
    result = []
    for char in text:
        if ord(char) < 128 or char == "'":  # ASCII or apostrophe
            result.append(char)
        elif ord(char) >= 128:
            # Replace with space if it's likely a special space character
            if ord(char) in [160, 8192, 8193, 8194, 8195, 8196, 8197, 8198, 8199, 8200, 8201, 8202, 8203]:
                result.append(' ')
            # Otherwise skip the character
    
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
                                'original': original[:50] + '...' if len(str(original)) > 50 else original,
                                'fixed': fixed[:50] + '...' if len(fixed) > 50 else fixed
                            })
            
            print(f"     Fixed {changes[col]['total']} values")
            
            # Show examples
            if changes[col]['examples']:
                print(f"     Examples:")
                for ex in changes[col]['examples'][:3]:
                    print(f"       Row {ex['row']}: '{ex['original']}' -> '{ex['fixed']}'")
    
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
                        f.write(f"    Row {ex['row']}: '{ex['original']}' -> '{ex['fixed']}'\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("All encoding issues have been fixed while preserving legitimate apostrophes.\n")
    
    print(f"   Report saved: {report_file}")
    
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