#!/usr/bin/env python3
"""
Comprehensive encoding issue scanner for Short descriptions
Created: 2025-09-03
Purpose: Systematically scan all Short descriptions in batches to identify ALL encoding issues
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def scan_batch(df, start_idx, end_idx, batch_num):
    """Scan a batch of rows for encoding issues"""
    
    issues = []
    char_frequency = defaultdict(int)
    
    for idx in range(start_idx, min(end_idx, len(df))):
        row_num = idx + 2  # Excel row number
        ig_id = df.at[idx, 'IG_ID']
        short_desc = df.at[idx, 'Short Deal Description']
        
        if pd.notna(short_desc) and short_desc != '':
            text = str(short_desc)
            
            # Scan each character
            for pos, char in enumerate(text):
                if ord(char) > 127:  # Non-ASCII character
                    char_frequency[char] += 1
                    
                    # Get context (10 chars before and after)
                    start = max(0, pos - 10)
                    end = min(len(text), pos + 11)
                    context = text[start:end]
                    
                    issues.append({
                        'batch': batch_num,
                        'row': row_num,
                        'ig_id': ig_id,
                        'position': pos,
                        'character': char,
                        'ascii_code': ord(char),
                        'hex_code': hex(ord(char)),
                        'context': context,
                        'full_text': text[:100] + '...' if len(text) > 100 else text
                    })
    
    return issues, char_frequency

def main():
    """Main execution function"""
    
    print("=" * 70)
    print("COMPREHENSIVE SHORT DESCRIPTION ENCODING SCAN")
    print("=" * 70)
    
    # Load data
    input_file = Path('../output/ig_arc_unmapped_FINAL_COMPLETE.csv')
    print(f"\n1. Loading data from: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8')
    total_rows = len(df)
    print(f"   Total rows: {total_rows}")
    
    # Calculate batches
    batch_size = 40
    num_batches = (total_rows + batch_size - 1) // batch_size
    print(f"   Processing in {num_batches} batches of {batch_size} rows")
    
    # Initialize tracking
    all_issues = []
    global_char_frequency = defaultdict(int)
    
    # Create report file
    report_file = Path('../output/ENCODING_ISSUES_SCAN_REPORT.md')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Short Deal Description Encoding Issues Scan Report\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Rows**: {total_rows}\n")
        f.write(f"**Batch Size**: {batch_size}\n")
        f.write(f"**Number of Batches**: {num_batches}\n\n")
        f.write("---\n\n")
        f.write("## Batch-by-Batch Scan Results\n\n")
        
        # Process each batch
        for batch_num in range(num_batches):
            start_idx = batch_num * batch_size
            end_idx = start_idx + batch_size
            
            print(f"\n2. Processing Batch {batch_num + 1}/{num_batches} (rows {start_idx + 2}-{min(end_idx + 1, total_rows + 1)})")
            
            # Scan this batch
            batch_issues, batch_chars = scan_batch(df, start_idx, end_idx, batch_num + 1)
            
            # Update global tracking
            all_issues.extend(batch_issues)
            for char, count in batch_chars.items():
                global_char_frequency[char] += count
            
            # Write batch results to report
            f.write(f"### Batch {batch_num + 1} (Rows {start_idx + 2}-{min(end_idx + 1, total_rows + 1)})\n")
            
            if batch_issues:
                f.write(f"- **Issues Found**: {len(batch_issues)}\n")
                f.write("- **Unique Characters**: ")
                unique_chars = list(set(issue['character'] for issue in batch_issues))
                for char in unique_chars[:10]:  # Show first 10
                    f.write(f"`{char}` (U+{ord(char):04X}) ")
                if len(unique_chars) > 10:
                    f.write(f"... and {len(unique_chars) - 10} more")
                f.write("\n\n")
                
                # Sample issues from this batch
                f.write("**Sample Issues:**\n")
                for issue in batch_issues[:5]:  # Show first 5 issues
                    f.write(f"- Row {issue['row']}: `{issue['character']}` at position {issue['position']}\n")
                    f.write(f"  Context: `...{issue['context']}...`\n")
            else:
                f.write("- **No encoding issues found**\n\n")
            
            print(f"   Found {len(batch_issues)} encoding issues")
            if batch_issues:
                print(f"   Unique characters: {len(set(issue['character'] for issue in batch_issues))}")
        
        # Write summary
        f.write("\n---\n\n")
        f.write("## Summary Statistics\n\n")
        f.write(f"- **Total Encoding Issues Found**: {len(all_issues)}\n")
        f.write(f"- **Affected Rows**: {len(set(issue['row'] for issue in all_issues))}\n")
        f.write(f"- **Unique Problematic Characters**: {len(global_char_frequency)}\n\n")
        
        # Character frequency table
        f.write("## Character Frequency Analysis\n\n")
        f.write("| Character | Unicode | Hex | Occurrences | Description |\n")
        f.write("|-----------|---------|-----|-------------|-------------|\n")
        
        # Sort by frequency
        sorted_chars = sorted(global_char_frequency.items(), key=lambda x: x[1], reverse=True)
        
        for char, count in sorted_chars[:50]:  # Top 50
            unicode_val = ord(char)
            hex_val = hex(unicode_val)
            
            # Try to identify the character
            desc = "Unknown"
            if unicode_val == 0x2019: desc = "Right single quotation mark"
            elif unicode_val == 0x2018: desc = "Left single quotation mark"
            elif unicode_val == 0x201C: desc = "Left double quotation mark"
            elif unicode_val == 0x201D: desc = "Right double quotation mark"
            elif unicode_val == 0x2014: desc = "Em dash"
            elif unicode_val == 0x2013: desc = "En dash"
            elif unicode_val == 0x20AC: desc = "Euro sign"
            elif unicode_val == 0xA3: desc = "Pound sign"
            elif unicode_val == 0x2122: desc = "Trademark"
            elif unicode_val == 0xAE: desc = "Registered"
            elif unicode_val == 0xA9: desc = "Copyright"
            elif unicode_val == 0x2026: desc = "Horizontal ellipsis"
            elif unicode_val == 0x2022: desc = "Bullet"
            elif unicode_val == 0xA0: desc = "Non-breaking space"
            elif 0xC0 <= unicode_val <= 0xFF: desc = "Latin-1 Supplement"
            elif 0x100 <= unicode_val <= 0x17F: desc = "Latin Extended-A"
            
            # Safe display of character
            try:
                char_display = char
            except:
                char_display = '?'
            
            f.write(f"| `{char_display}` | U+{unicode_val:04X} | {hex_val} | {count} | {desc} |\n")
        
        if len(sorted_chars) > 50:
            f.write(f"\n*... and {len(sorted_chars) - 50} more unique characters*\n")
        
        # Affected rows list
        f.write("\n## Affected Rows\n\n")
        affected_rows = sorted(set(issue['row'] for issue in all_issues))
        f.write(f"Total affected rows: {len(affected_rows)}\n\n")
        f.write("Row numbers: ")
        f.write(', '.join(str(r) for r in affected_rows[:100]))
        if len(affected_rows) > 100:
            f.write(f"... and {len(affected_rows) - 100} more")
        f.write("\n")
    
    # Save detailed JSON data
    json_file = Path('../output/encoding_issues_detailed.json')
    
    # Create character mapping suggestions
    char_mapping = {}
    for char in global_char_frequency.keys():
        unicode_val = ord(char)
        
        # Suggest replacements based on Unicode value
        if unicode_val == 0x2019 or unicode_val == 0x2018:  # Smart quotes
            char_mapping[char] = "'"
        elif unicode_val == 0x201C or unicode_val == 0x201D:  # Smart double quotes
            char_mapping[char] = '"'
        elif unicode_val == 0x2014:  # Em dash
            char_mapping[char] = "-"
        elif unicode_val == 0x2013:  # En dash
            char_mapping[char] = "-"
        elif unicode_val == 0x20AC:  # Euro
            char_mapping[char] = "EUR"
        elif unicode_val == 0xA3:  # Pound
            char_mapping[char] = "GBP"
        elif unicode_val == 0x2122:  # Trademark
            char_mapping[char] = "(TM)"
        elif unicode_val == 0xAE:  # Registered
            char_mapping[char] = "(R)"
        elif unicode_val == 0xA9:  # Copyright
            char_mapping[char] = "(c)"
        elif unicode_val == 0x2026:  # Ellipsis
            char_mapping[char] = "..."
        elif unicode_val == 0x2022:  # Bullet
            char_mapping[char] = "*"
        elif unicode_val == 0xA0:  # Non-breaking space
            char_mapping[char] = " "
        elif unicode_val == 0xD7:  # Multiplication sign
            char_mapping[char] = "x"
        elif unicode_val == 0xF7:  # Division sign
            char_mapping[char] = "/"
        elif unicode_val == 0xB1:  # Plus-minus
            char_mapping[char] = "+/-"
        else:
            # For other characters, try to normalize
            char_mapping[char] = ""  # Will need manual review
    
    # Save JSON data
    json_data = {
        'scan_date': datetime.now().isoformat(),
        'total_rows': total_rows,
        'total_issues': len(all_issues),
        'affected_rows': len(affected_rows),
        'unique_characters': len(global_char_frequency),
        'character_frequency': {char: count for char, count in sorted_chars},
        'character_mapping': char_mapping,
        'sample_issues': all_issues[:100]  # First 100 issues
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print("SCAN COMPLETE!")
    print("=" * 70)
    print(f"\nResults:")
    print(f"  Total issues found: {len(all_issues)}")
    print(f"  Affected rows: {len(affected_rows)} of {total_rows}")
    print(f"  Unique problematic characters: {len(global_char_frequency)}")
    print(f"\nReports generated:")
    print(f"  - {report_file}")
    print(f"  - {json_file}")
    
    return json_data

if __name__ == "__main__":
    results = main()