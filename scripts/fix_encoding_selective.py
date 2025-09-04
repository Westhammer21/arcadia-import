#!/usr/bin/env python3
"""
Script to fix UTF-8 encoding issues while preserving apostrophes in names
Created: 2025-09-03
Purpose: Convert special characters to ASCII while keeping apostrophes that are part of names
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# UTF-8 to ASCII mapping - EXCLUDING apostrophes
UTF8_FIXES = {
    # Accented characters
    'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a', 'æ': 'ae',
    'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A', 'Å': 'A', 'Æ': 'AE',
    'ç': 'c', 'Ç': 'C',
    'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
    'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
    'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
    'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I',
    'ñ': 'n', 'Ñ': 'N',
    'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o', 'ø': 'o',
    'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O', 'Ø': 'O',
    'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
    'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U',
    'ý': 'y', 'ÿ': 'y', 'Ý': 'Y', 'Ÿ': 'Y',
    
    # Special characters
    'ß': 'ss', 'þ': 'th', 'Þ': 'TH', 'ð': 'd', 'Ð': 'D',
    'ı': 'i', 'ğ': 'g', 'Ğ': 'G', 'ş': 's', 'Ş': 'S',
    'č': 'c', 'Č': 'C', 'ď': 'd', 'Ď': 'D', 'ě': 'e', 'Ě': 'E',
    'ň': 'n', 'Ň': 'N', 'ř': 'r', 'Ř': 'R', 'š': 's', 'Š': 'S',
    'ť': 't', 'Ť': 'T', 'ů': 'u', 'Ů': 'U', 'ž': 'z', 'Ž': 'Z',
    'ą': 'a', 'Ą': 'A', 'ć': 'c', 'Ć': 'C', 'ę': 'e', 'Ę': 'E',
    'ł': 'l', 'Ł': 'L', 'ń': 'n', 'Ń': 'N', 'ś': 's', 'Ś': 'S',
    'ź': 'z', 'Ź': 'Z', 'ż': 'z', 'Ż': 'Z',
    
    # Cyrillic characters (common ones)
    'а': 'a', 'А': 'A', 'б': 'b', 'Б': 'B', 'в': 'v', 'В': 'V',
    'г': 'g', 'Г': 'G', 'д': 'd', 'Д': 'D', 'е': 'e', 'Е': 'E',
    'ё': 'e', 'Ё': 'E', 'ж': 'zh', 'Ж': 'ZH', 'з': 'z', 'З': 'Z',
    'и': 'i', 'И': 'I', 'й': 'y', 'Й': 'Y', 'к': 'k', 'К': 'K',
    'л': 'l', 'Л': 'L', 'м': 'm', 'М': 'M', 'н': 'n', 'Н': 'N',
    'о': 'o', 'О': 'O', 'п': 'p', 'П': 'P', 'р': 'r', 'Р': 'R',
    'с': 's', 'С': 'S', 'т': 't', 'Т': 'T', 'у': 'u', 'У': 'U',
    'ф': 'f', 'Ф': 'F', 'х': 'h', 'Х': 'H', 'ц': 'ts', 'Ц': 'TS',
    'ч': 'ch', 'Ч': 'CH', 'ш': 'sh', 'Ш': 'SH', 'щ': 'sch', 'Щ': 'SCH',
    'ъ': '', 'Ъ': '', 'ы': 'y', 'Ы': 'Y', 'ь': '', 'Ь': '',
    'э': 'e', 'Э': 'E', 'ю': 'yu', 'Ю': 'YU', 'я': 'ya', 'Я': 'YA',
    
    # Mathematical and special symbols
    '²': '2', '³': '3', '°': ' degrees', '€': 'EUR', '£': 'GBP',
    '¥': 'JPY', '₹': 'INR', '₽': 'RUB', '¢': 'c', '§': 'S',
    '©': '(c)', '®': '(R)', '™': '(TM)', '×': 'x', '÷': '/',
    '±': '+/-', '¼': '1/4', '½': '1/2', '¾': '3/4',
    '≈': '~', '≠': '!=', '≤': '<=', '≥': '>=',
    '•': '-', '…': '...', '–': '-', '—': '-',
    '"': '"', '"': '"', ''': "'", ''': "'",  # Smart quotes to regular
    '«': '"', '»': '"', '‹': '<', '›': '>',
    
    # Note: Apostrophe (') is NOT included in replacements
}

def fix_text_selective(text):
    """Fix encoding issues while preserving apostrophes"""
    if pd.isna(text) or text == '':
        return text
    
    # Convert to string if not already
    text = str(text)
    
    # Apply all fixes EXCEPT apostrophes
    for old_char, new_char in UTF8_FIXES.items():
        text = text.replace(old_char, new_char)
    
    # Clean up extra spaces
    text = ' '.join(text.split())
    
    return text

def analyze_changes(df, fixed_df, columns_to_fix):
    """Analyze what changes were made"""
    changes_summary = {}
    
    for col in columns_to_fix:
        changed_mask = df[col].astype(str) != fixed_df[col].astype(str)
        changed_count = changed_mask.sum()
        
        if changed_count > 0:
            changes_summary[col] = {
                'count': changed_count,
                'examples': []
            }
            
            # Get up to 5 examples
            changed_indices = df[changed_mask].head(5).index
            for idx in changed_indices:
                original = str(df.at[idx, col])[:100]  # Truncate for display
                fixed = str(fixed_df.at[idx, col])[:100]
                changes_summary[col]['examples'].append({
                    'original': original,
                    'fixed': fixed,
                    'row': idx + 2  # Excel row number (header is row 1)
                })
    
    return changes_summary

def verify_data_integrity(original_df, fixed_df):
    """Verify that data structure is maintained correctly"""
    issues = []
    
    # Check row count
    if len(original_df) != len(fixed_df):
        issues.append(f"Row count mismatch: Original={len(original_df)}, Fixed={len(fixed_df)}")
    
    # Check column count and names
    if list(original_df.columns) != list(fixed_df.columns):
        issues.append("Column structure changed")
    
    # Check critical ID column
    if 'IG_ID' in original_df.columns:
        if not original_df['IG_ID'].equals(fixed_df['IG_ID']):
            issues.append("IG_ID values changed or misaligned")
    
    # Check mapped columns haven't changed
    for col in ['Mapped_Type', 'Mapped_Category']:
        if col in original_df.columns:
            if not original_df[col].equals(fixed_df[col]):
                issues.append(f"{col} values changed unexpectedly")
    
    # Check numeric columns haven't changed
    for col in ['Size, $m', 'Year', 'Target Founded']:
        if col in original_df.columns:
            orig_vals = original_df[col].fillna(-999)
            fixed_vals = fixed_df[col].fillna(-999)
            if not np.allclose(orig_vals, fixed_vals, rtol=1e-5, equal_nan=True):
                issues.append(f"{col} numeric values changed")
    
    return issues

def main():
    """Main execution function"""
    
    print("=" * 70)
    print("SELECTIVE ENCODING FIX FOR UNMAPPED IG DATA")
    print("Preserving apostrophes while fixing other UTF-8 issues")
    print("=" * 70)
    
    # File paths
    input_file = Path('../output/ig_arc_unmapped_final.csv')
    backup_file = Path(f'../output/ig_arc_unmapped_final_BACKUP_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    output_file = Path('../output/ig_arc_unmapped_final_fixed.csv')
    
    # Read the file
    print(f"\n1. Reading file: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"   Total records: {len(df)}")
    print(f"   Total columns: {len(df.columns)}")
    
    # Create backup
    print(f"\n2. Creating backup: {backup_file}")
    df.to_csv(backup_file, index=False, encoding='utf-8')
    
    # Create a copy for fixing
    df_fixed = df.copy()
    
    # Define columns to fix (text columns only)
    columns_to_fix = ['Target name', 'Investors / Buyers', 'Short Deal Description']
    
    print("\n3. Applying selective encoding fixes")
    print("   Preserving: Apostrophes (')")
    print("   Fixing: All other special characters")
    
    # Apply fixes to specified columns
    for col in columns_to_fix:
        if col in df_fixed.columns:
            print(f"   Processing column: {col}")
            df_fixed[col] = df_fixed[col].apply(fix_text_selective)
    
    # Analyze changes
    print("\n4. Analyzing changes")
    changes = analyze_changes(df, df_fixed, columns_to_fix)
    
    total_changes = sum(c['count'] for c in changes.values())
    print(f"   Total records with changes: {total_changes}")
    
    for col, info in changes.items():
        print(f"\n   {col}: {info['count']} changes")
        for ex in info['examples'][:3]:  # Show up to 3 examples
            print(f"     Row {ex['row']}:")
            print(f"       Before: {ex['original'][:60]}...")
            print(f"       After:  {ex['fixed'][:60]}...")
    
    # Verify data integrity
    print("\n5. Verifying data integrity")
    issues = verify_data_integrity(df, df_fixed)
    
    if issues:
        print("   WARNING: Data integrity issues detected:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n   Aborting to prevent data corruption!")
        return
    else:
        print("   OK: All data integrity checks passed")
        print(f"   - Row count maintained: {len(df_fixed)} records")
        print(f"   - Column structure preserved: {len(df_fixed.columns)} columns")
        print("   - ID alignment verified")
        print("   - Mapped values unchanged")
    
    # Check apostrophe preservation
    print("\n6. Verifying apostrophe preservation")
    apostrophe_examples = []
    for col in columns_to_fix:
        if col in df_fixed.columns:
            mask = df_fixed[col].astype(str).str.contains("'", na=False)
            count = mask.sum()
            if count > 0:
                examples = df_fixed[mask][col].head(3).tolist()
                apostrophe_examples.extend(examples)
                print(f"   {col}: {count} entries with apostrophes preserved")
    
    if apostrophe_examples:
        print("   Examples of preserved apostrophes:")
        for ex in apostrophe_examples[:5]:
            print(f"     - {ex[:80]}")
    
    # Save the fixed file
    print(f"\n7. Saving fixed file: {output_file}")
    df_fixed.to_csv(output_file, index=False, encoding='utf-8')
    print("   File saved successfully!")
    
    # Create summary report
    report_file = Path('../output/encoding_fix_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("SELECTIVE ENCODING FIX REPORT\n")
        f.write("=" * 70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Input: {input_file}\n")
        f.write(f"Output: {output_file}\n\n")
        
        f.write("SUMMARY\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total records: {len(df_fixed)}\n")
        f.write(f"Records with changes: {total_changes}\n")
        f.write(f"Apostrophes preserved: Yes\n")
        f.write(f"Other UTF-8 issues fixed: Yes\n\n")
        
        f.write("CHANGES BY COLUMN\n")
        f.write("-" * 70 + "\n")
        for col, info in changes.items():
            f.write(f"\n{col}: {info['count']} changes\n")
            for ex in info['examples']:
                f.write(f"  Row {ex['row']}: {ex['original'][:50]}... → {ex['fixed'][:50]}...\n")
    
    print(f"\n   Report saved: {report_file}")
    
    print("\n" + "=" * 70)
    print("SELECTIVE ENCODING FIX COMPLETE!")
    print("=" * 70)
    
    return {
        'total_records': len(df_fixed),
        'records_changed': total_changes,
        'apostrophes_preserved': True,
        'output_file': str(output_file)
    }

if __name__ == "__main__":
    result = main()