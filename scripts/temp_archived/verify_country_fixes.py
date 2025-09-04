#!/usr/bin/env python3
"""Verify the country mapping fixes"""

import pandas as pd

# Read the fixed file
df = pd.read_csv('output/ig_arc_unmapped_FINAL_COMPLETE.csv', dtype=str, na_filter=False)

# Filter TO BE CREATED records
to_be_created = df[df['arc_id'] == 'TO BE CREATED'].copy()

print(f"Total TO BE CREATED records: {len(to_be_created)}")
print()

# Check for remaining notenoughinformation
noinfo = to_be_created[to_be_created['arc_hq_country'] == 'notenoughinformation']
print(f"Remaining 'notenoughinformation' records: {len(noinfo)}")

if len(noinfo) > 0:
    print("\nRecords still with 'notenoughinformation':")
    for idx, row in noinfo.iterrows():
        print(f"  Row {idx+2}: {row['Target name']}")
        targets_country = row["Target's Country"]
        print(f"    Target's Country: '{targets_country}'")
        print()

# Check for 2-letter codes
print("\nUnique arc_hq_country values for TO BE CREATED records:")
country_counts = to_be_created['arc_hq_country'].value_counts().sort_index()
for country, count in country_counts.items():
    # Flag if it looks like a 2-letter code
    flag = " (possible ISO code)" if len(country) == 2 else ""
    print(f"  {country}: {count} records{flag}")

print()

# Check specific countries mentioned by user
specific_countries = ['Estonia', 'Cyprus', 'Kazakhstan', 'Saudi Arabia', 'United Arab Emirates', 'Jordan', 'Egypt', 'Sweden', 'South Korea', 'United Kingdom']
print("Specific country mappings check:")
for country in specific_countries:
    # Check if Target's Country has this value
    with_target_country = to_be_created[to_be_created["Target's Country"] == country]
    if len(with_target_country) > 0:
        print(f"\n  Records where Target's Country = '{country}':")
        for idx, row in with_target_country.iterrows():
            print(f"    Row {idx+2}: {row['Target name']}")
            print(f"      arc_hq_country: '{row['arc_hq_country']}'")

print("\n" + "="*60)
print("Summary:")
print("="*60)

# Count properly mapped vs unmapped
properly_mapped = to_be_created[
    (to_be_created['arc_hq_country'] != 'notenoughinformation') & 
    (to_be_created['arc_hq_country'].str.len() > 2)
]
print(f"[OK] Properly mapped (full country names): {len(properly_mapped)}")
print(f"[REMAINING] Still with 'notenoughinformation': {len(noinfo)}")

# Check for any remaining 2-letter codes
two_letter = to_be_created[to_be_created['arc_hq_country'].str.len() == 2]
if len(two_letter) > 0:
    print(f"[ERROR] Still with 2-letter codes: {len(two_letter)}")
    print("  Details:")
    for idx, row in two_letter.iterrows():
        print(f"    Row {idx+2}: {row['Target name']} -> '{row['arc_hq_country']}'")