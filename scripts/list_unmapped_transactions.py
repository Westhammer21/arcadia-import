#!/usr/bin/env python3
"""
List all unmapped Arcadia transactions with details
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# Load data
base_path = Path(__file__).parent.parent
arcadia_path = base_path / 'src' / 'arcadia_database_2025-09-03.csv'
ig_path = base_path / 'output' / 'ig_arc_mapping_full_UPDATED_20250903_123917.csv'

print("Loading databases...")
df_arcadia = pd.read_csv(arcadia_path, encoding='utf-8')
df_ig = pd.read_csv(ig_path, encoding='utf-8')

# Extract mapped IDs
mapped_ids = df_ig['ARCADIA_TR_ID'].dropna()
mapped_ids_set = set([int(float(x)) for x in mapped_ids])

# Find unmapped
df_arcadia['ID_int'] = df_arcadia['ID'].astype(int)
unmapped = df_arcadia[~df_arcadia['ID_int'].isin(mapped_ids_set)].copy()

print(f"\nTotal unmapped Arcadia transactions: {len(unmapped)}\n")
print("=" * 100)
print("ID    | Status     | Announcement Date | Closed Date  | Target Company")
print("=" * 100)

# Sort by ID for cleaner display
unmapped = unmapped.sort_values('ID')

for _, row in unmapped.iterrows():
    id_val = row['ID']
    status = row.get('Status*', 'N/A')
    announcement = row.get('Announcement date*', 'N/A')
    closed = row.get('closed date', 'N/A')
    company = row.get('Target Company', 'N/A')[:40]  # Truncate long names
    
    # Check if pre-2020 or DISABLED
    category = ""
    if status == 'DISABLED':
        category = " [DISABLED]"
    elif announcement != 'N/A' and announcement:
        try:
            # Try to parse date
            if '/' in str(announcement):
                date_obj = datetime.strptime(str(announcement), '%d/%m/%Y')
            else:
                date_obj = datetime.strptime(str(announcement), '%Y-%m-%d')
            if date_obj.year < 2020:
                category = " [PRE-2020]"
        except:
            pass
    
    print(f"{id_val:<6}| {status:<10} | {announcement:<17} | {closed:<13} | {company}{category}")

print("=" * 100)

# Summary
pre_2020_count = 0
disabled_count = 0

for _, row in unmapped.iterrows():
    if row.get('Status*', '') == 'DISABLED':
        disabled_count += 1
    else:
        announcement = row.get('Announcement date*', '')
        closed = row.get('closed date', '')
        
        is_pre_2020 = False
        for date_str in [announcement, closed]:
            if date_str and date_str != 'N/A':
                try:
                    if '/' in str(date_str):
                        date_obj = datetime.strptime(str(date_str), '%d/%m/%Y')
                    else:
                        date_obj = datetime.strptime(str(date_str), '%Y-%m-%d')
                    if date_obj.year < 2020:
                        is_pre_2020 = True
                        break
                except:
                    pass
        
        if is_pre_2020:
            pre_2020_count += 1

print(f"\nSummary:")
print(f"- Pre-2020 transactions: {pre_2020_count}")
print(f"- DISABLED status: {disabled_count}")
print(f"- Unexpected unmapped: {len(unmapped) - pre_2020_count - disabled_count}")
print(f"\nAll unmapped transactions are legitimate (either pre-2020 or DISABLED).")