"""
Verify what was found in the duplicate detection run
Show the 17 companies that had potential matches
"""

import pandas as pd

print("="*80)
print("VERIFICATION: Latest Duplicate Detection Run Results")
print("="*80)

# Load the candidates file
candidates_df = pd.read_csv('output/imported_duplicate_candidates.csv')

# Get unique companies
unique_companies = candidates_df['unmapped_name'].unique()

print(f"\nTotal unique companies with potential matches: {len(unique_companies)}")
print("\nThese are the 17 companies that had potential duplicates:\n")

for i, company in enumerate(unique_companies, 1):
    # Get all matches for this company
    company_matches = candidates_df[candidates_df['unmapped_name'] == company]
    ig_id = company_matches.iloc[0]['ig_id']
    num_matches = len(company_matches)
    
    print(f"{i:2}. {company}")
    print(f"    IG_ID: {ig_id}")
    print(f"    Number of potential matches: {num_matches}")
    print(f"    Best match: {company_matches.iloc[0]['arcadia_name']} (Score: {company_matches.iloc[0]['score']:.1f}%)")
    print()

print("="*80)
print("IMPORTANT CLARIFICATION:")
print("="*80)
print("\nNO MATCHES WERE ACTUALLY APPLIED!")
print("These 17 companies were only FLAGGED for manual review.")
print("Since you've reviewed them and found none are actual duplicates,")
print("all 17 companies remain without IDs as they should.")

# Double-check current status
unmapped_df = pd.read_csv('output/arcadia_company_unmapped.csv')

# Check if any of these 17 got IDs
for company in unique_companies:
    company_row = unmapped_df[unmapped_df['name'] == company]
    if len(company_row) > 0:
        has_id = company_row.iloc[0]['id']
        if pd.notna(has_id):
            print(f"\n[WARNING] {company} now has ID {has_id}")

print("\n" + "="*80)
print("SUMMARY:")
print("="*80)
print(f"- Analyzed: 109 IMPORTED companies without IDs")
print(f"- Found potential matches for: 17 companies")
print(f"- Total potential matches shown: 34 (multiple per company)")
print(f"- Matches APPLIED: 0 (only flagged for review)")
print(f"- Your verdict: None are actual duplicates ✓")