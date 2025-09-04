#!/usr/bin/env python3
"""Final verification of country mapping fixes"""

import pandas as pd

# Read the file
df = pd.read_csv('output/ig_arc_unmapped_FINAL_COMPLETE.csv', dtype=str, na_filter=False)

# Filter TO BE CREATED records
to_be_created = df[df['arc_id'] == 'TO BE CREATED'].copy()

print("="*60)
print("FINAL VERIFICATION REPORT")
print("="*60)
print(f"Total TO BE CREATED records: {len(to_be_created)}")
print()

# Check for notenoughinformation
noinfo = to_be_created[to_be_created['arc_hq_country'] == 'notenoughinformation']
print(f"Records with 'notenoughinformation': {len(noinfo)}")
if len(noinfo) > 0:
    print("  (These have empty Target's Country values)")
    for idx, row in noinfo.iterrows():
        print(f"  - Row {idx+2}: {row['Target name']}")

print()

# Check for 2-letter codes
two_letter = to_be_created[to_be_created['arc_hq_country'].str.len() == 2]
print(f"Records with 2-letter ISO codes: {len(two_letter)}")
if len(two_letter) > 0:
    print("  ERROR - Still have 2-letter codes:")
    for idx, row in two_letter.iterrows():
        print(f"  - Row {idx+2}: {row['Target name']} -> {row['arc_hq_country']}")

print()

# Count by country
print("Country distribution for TO BE CREATED records:")
country_counts = to_be_created['arc_hq_country'].value_counts().sort_values(ascending=False)
for country, count in country_counts.items():
    if country != 'notenoughinformation':
        print(f"  {country}: {count}")

print()
print("="*60)
print("SUMMARY:")
print("="*60)

# Calculate success metrics
total_records = len(to_be_created)
properly_mapped = len(to_be_created[
    (to_be_created['arc_hq_country'] != 'notenoughinformation') & 
    (to_be_created['arc_hq_country'].str.len() > 2)
])
success_rate = (properly_mapped / total_records) * 100

print(f"Total TO BE CREATED records: {total_records}")
print(f"Successfully mapped to full country names: {properly_mapped}")
print(f"Remaining with 'notenoughinformation': {len(noinfo)}")
print(f"Remaining with 2-letter ISO codes: {len(two_letter)}")
print(f"Success rate: {success_rate:.1f}%")

if len(two_letter) == 0 and success_rate > 95:
    print("\n[SUCCESS] All 2-letter ISO codes have been converted to full country names!")
    print("[SUCCESS] Country mapping fix completed successfully!")