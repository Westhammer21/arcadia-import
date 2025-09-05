"""
Explain the 34 total matches - breakdown by company
"""

import pandas as pd

# Load the candidates file
candidates_df = pd.read_csv('output/imported_duplicate_candidates.csv')

print("="*80)
print("EXPLANATION: The 34 Total Matches Breakdown")
print("="*80)
print("\nEach company could have up to 3 potential matches shown.")
print("The 34 is the TOTAL of all these potential matches:\n")

# Group by company and count
company_counts = candidates_df.groupby('unmapped_name').size().reset_index(name='match_count')
company_counts = company_counts.sort_values('match_count', ascending=False)

total = 0
for _, row in company_counts.iterrows():
    company = row['unmapped_name']
    count = row['match_count']
    total += count
    
    # Get the matches for this company
    matches = candidates_df[candidates_df['unmapped_name'] == company]
    
    print(f"{company}: {count} matches")
    for _, match in matches.iterrows():
        score = match['score']
        arcadia_name = match['arcadia_name']
        print(f"  -> {arcadia_name} ({score:.1f}%)")
    print()

print("="*80)
print(f"TOTAL: {total} matches across {len(company_counts)} companies")
print("="*80)

print("\nBreakdown by number of matches per company:")
match_distribution = company_counts['match_count'].value_counts().sort_index()
for num_matches, num_companies in match_distribution.items():
    print(f"  - {num_companies} companies had {num_matches} match(es) each = {num_companies * num_matches} total matches")

print(f"\nSum: {sum(match_distribution.index * match_distribution.values)} total matches")