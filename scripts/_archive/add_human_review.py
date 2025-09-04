import pandas as pd
import numpy as np

print("=" * 80)
print("ADDING HUMAN REVIEW COLUMN TO ADVANCED ANALYSIS")
print("=" * 80)

# Load the advanced results
df = pd.read_csv('../output/test_description_advanced.csv')
print(f"\nLoaded {len(df)} records")

# Show distribution
print(f"\nMatch Category Distribution:")
print(df['Match_Category'].value_counts())

# Add Human_checked column
df['Human_checked'] = ''

# Mark clear matches (High/Medium/Low similarity and Exact matches)
match_categories = ['Exact Match', 'High Similarity (90-100%)', 
                   'Medium Similarity (70-90%)', 'Low Similarity (50-70%)']

matches_count = 0
for category in match_categories:
    mask = df['Match_Category'] == category
    df.loc[mask, 'Human_checked'] = 'MATCH'
    count = mask.sum()
    matches_count += count
    print(f"\nMarked {count} records as MATCH for: {category}")

# Mark missing data
missing_mask = df['Match_Category'] == 'Missing Data'
df.loc[missing_mask, 'Human_checked'] = 'NO_DATA'
print(f"\nMarked {missing_mask.sum()} records as NO_DATA (missing descriptions)")

# Very Low similarity cases need manual review
very_low_mask = df['Match_Category'] == 'Very Low Similarity (<50%)'
very_low_count = very_low_mask.sum()
print(f"\n{very_low_count} Very Low similarity cases need manual review")

# Show summary
print(f"\nHuman_checked summary so far:")
print(df['Human_checked'].value_counts())

# Get Very Low similarity cases for manual review
very_low_df = df[very_low_mask].copy()
print(f"\n\nFILTERING VERY LOW SIMILARITY CASES FOR MANUAL REVIEW:")
print(f"Found {len(very_low_df)} cases with <50% similarity")

# Save the full dataframe with Human_checked column (will update after manual review)
output_file = '../output/test_description_advanced_human.csv'
df.to_csv(output_file, index=False)
print(f"\nSaved initial file to: {output_file}")

# Save Very Low cases for review
review_file = '../output/very_low_similarity_for_review.csv'
very_low_df.to_csv(review_file, index=False)
print(f"Saved {len(very_low_df)} Very Low cases to: {review_file}")

print("\n" + "=" * 80)
print("READY FOR MANUAL FINANCIAL EXPERT REVIEW")
print("=" * 80)