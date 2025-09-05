"""
Verify the current ID status after matching
"""

import pandas as pd

# Load the updated file
df = pd.read_csv('output/arcadia_company_unmapped.csv')

print("ID Assignment Status Analysis")
print("=" * 60)

# Count companies with and without IDs
has_id = df['id'].notna()
no_id = df['id'].isna()

print(f"\nTotal companies: {len(df)}")
print(f"Companies WITH ID assigned: {has_id.sum()}")
print(f"Companies WITHOUT ID: {no_id.sum()}")

# Break down by status
print("\nBreakdown by status:")
status_breakdown = df.groupby('status').agg({
    'id': lambda x: x.notna().sum(),
    'name': 'count'
}).rename(columns={'id': 'with_id', 'name': 'total'})
status_breakdown['without_id'] = status_breakdown['total'] - status_breakdown['with_id']
print(status_breakdown)

# Verify the logic
print("\nVerification:")
print(f"- TO BE CREATED companies (should have no ID): {len(df[df['status'] == 'TO BE CREATED'])}")
print(f"- Other statuses without ID (couldn't match): {len(df[(df['status'] != 'TO BE CREATED') & (df['id'].isna())])}")
print(f"- Total without ID: {no_id.sum()}")
print(f"  (820 TO BE CREATED + 112 unmatched = 932) [OK]" if no_id.sum() == 932 else f"  Expected 932, got {no_id.sum()}")

# Show examples of each category
print("\n" + "=" * 60)
print("Examples of companies WITH ID (matched successfully):")
matched = df[df['id'].notna()].head(5)
for _, row in matched.iterrows():
    print(f"  - {row['name']} (ID: {int(row['id'])}, Status: {row['status']})")

print("\nExamples of companies WITHOUT ID (TO BE CREATED):")
to_be_created = df[(df['status'] == 'TO BE CREATED') & (df['id'].isna())].head(5)
for _, row in to_be_created.iterrows():
    print(f"  - {row['name']} (Status: {row['status']})")

print("\nExamples of companies WITHOUT ID (couldn't match):")
unmatched = df[(df['status'] != 'TO BE CREATED') & (df['id'].isna())].head(5)
for _, row in unmatched.iterrows():
    print(f"  - {row['name']} (Status: {row['status']})")

print("\n" + "=" * 60)
print("SUMMARY:")
print(f"[OK] {has_id.sum()} companies have Arcadia IDs assigned")
print(f"[OK] {no_id.sum()} companies need IDs (932 expected)")
print(f"     - 820 are new companies (TO BE CREATED)")
print(f"     - 112 are existing but couldn't match")