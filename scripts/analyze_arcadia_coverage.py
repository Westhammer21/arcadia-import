import pandas as pd
from datetime import datetime
import numpy as np

print("=" * 80)
print("ARCADIA DATABASE COVERAGE ANALYSIS")
print("=" * 80)

# 1. Read Arcadia database
print("\n1. Reading Arcadia database...")
arcadia_file = 'src/arcadia_database_2025-09-01.csv'
df_arcadia = pd.read_csv(arcadia_file, sep='\t')
print(f"   Total Arcadia transactions: {len(df_arcadia)}")

# 2. Parse dates - handle different date formats
print("\n2. Parsing date columns...")

def parse_date(date_str):
    """Parse date from DD/MM/YYYY or MM/DD/YYYY format"""
    if pd.isna(date_str) or date_str == '' or date_str == '0':
        return None
    
    date_str = str(date_str).strip()
    
    # Try DD/MM/YYYY format first (most common in this data)
    try:
        return datetime.strptime(date_str, '%d/%m/%Y')
    except:
        pass
    
    # Try MM/DD/YYYY format
    try:
        return datetime.strptime(date_str, '%m/%d/%Y')
    except:
        pass
    
    # Try YYYY-MM-DD format
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        pass
    
    return None

# Apply date parsing
df_arcadia['announcement_date_parsed'] = df_arcadia['Announcement date*'].apply(parse_date)
df_arcadia['closed_date_parsed'] = df_arcadia['closed date'].apply(parse_date)

# Count successful date parsing
announced_dates = df_arcadia['announcement_date_parsed'].notna().sum()
closed_dates = df_arcadia['closed_date_parsed'].notna().sum()
print(f"   Successfully parsed announcement dates: {announced_dates}/{len(df_arcadia)}")
print(f"   Successfully parsed closed dates: {closed_dates}/{len(df_arcadia)}")

# 3. Categorize transactions by date
print("\n3. Categorizing transactions by date...")
cutoff_date = datetime(2020, 1, 1)

# A transaction is pre-2020 if EITHER announcement OR closed date is before 2020
def categorize_transaction(row):
    ann_date = row['announcement_date_parsed']
    close_date = row['closed_date_parsed']
    
    # Check if either date is before 2020
    if (ann_date and ann_date < cutoff_date) or (close_date and close_date < cutoff_date):
        return 'pre-2020'
    
    # If both dates are None, we can't determine, treat as post-2020
    if ann_date is None and close_date is None:
        return 'unknown-date'
    
    # If we have at least one date and it's >= 2020
    return 'post-2020'

df_arcadia['date_category'] = df_arcadia.apply(categorize_transaction, axis=1)

# Count by category
category_counts = df_arcadia['date_category'].value_counts()
print("\n   Date Categories:")
for cat, count in category_counts.items():
    print(f"   {cat}: {count} ({count/len(df_arcadia)*100:.1f}%)")

# 4. Read mapping file to get mapped Arcadia IDs
print("\n4. Reading mapping file...")
mapping_file = 'output/ig_arc_mapping_full.csv'
df_mapping = pd.read_csv(mapping_file)

# Get mapped Arcadia IDs (non-null ARC_ID values)
mapped_arc_ids = df_mapping[df_mapping['ARC_ID'].notna()]['ARC_ID'].astype(int).unique()
print(f"   Total unique Arcadia IDs in mapping: {len(mapped_arc_ids)}")

# 5. Check coverage
print("\n5. COVERAGE ANALYSIS:")
print("-" * 60)

# Overall coverage
arcadia_ids = set(df_arcadia['ID'].values)
mapped_ids = set(mapped_arc_ids)
mapped_in_arcadia = arcadia_ids.intersection(mapped_ids)

print("\n   OVERALL COVERAGE:")
print(f"   Total Arcadia transactions: {len(df_arcadia)}")
print(f"   Mapped Arcadia transactions: {len(mapped_in_arcadia)}")
print(f"   Overall coverage: {len(mapped_in_arcadia)/len(df_arcadia)*100:.1f}%")

# Coverage by date category
print("\n   COVERAGE BY DATE CATEGORY:")
for category in ['pre-2020', 'post-2020', 'unknown-date']:
    cat_data = df_arcadia[df_arcadia['date_category'] == category]
    if len(cat_data) > 0:
        cat_ids = set(cat_data['ID'].values)
        cat_mapped = cat_ids.intersection(mapped_ids)
        print(f"\n   {category.upper()}:")
        print(f"   Total: {len(cat_data)} transactions")
        print(f"   Mapped: {len(cat_mapped)} transactions")
        print(f"   Coverage: {len(cat_mapped)/len(cat_data)*100:.1f}%")
        
        # For pre-2020, list any that ARE mapped (shouldn't be many/any)
        if category == 'pre-2020' and len(cat_mapped) > 0:
            print(f"   WARNING: {len(cat_mapped)} pre-2020 transactions are mapped!")
            print(f"   Pre-2020 mapped IDs (first 10): {list(cat_mapped)[:10]}")

# 6. Detailed year-by-year analysis for post-2020
print("\n6. YEAR-BY-YEAR ANALYSIS (Post-2020):")
print("-" * 60)

# Extract year from dates
df_arcadia['year'] = df_arcadia['announcement_date_parsed'].apply(
    lambda x: x.year if pd.notna(x) else None
)

# For transactions with no announcement date, try closed date
mask = df_arcadia['year'].isna()
df_arcadia.loc[mask, 'year'] = df_arcadia.loc[mask, 'closed_date_parsed'].apply(
    lambda x: x.year if pd.notna(x) else None
)

# Analyze by year for 2020+
for year in range(2020, 2026):
    year_data = df_arcadia[df_arcadia['year'] == year]
    if len(year_data) > 0:
        year_ids = set(year_data['ID'].values)
        year_mapped = year_ids.intersection(mapped_ids)
        print(f"\n   Year {year}:")
        print(f"   Total: {len(year_data)} transactions")
        print(f"   Mapped: {len(year_mapped)} transactions")
        print(f"   Coverage: {len(year_mapped)/len(year_data)*100:.1f}%")

# 7. Find unmapped post-2020 transactions
print("\n7. UNMAPPED POST-2020 TRANSACTIONS:")
print("-" * 60)
post_2020 = df_arcadia[df_arcadia['date_category'] == 'post-2020']
post_2020_ids = set(post_2020['ID'].values)
unmapped_post_2020 = post_2020_ids - mapped_ids

print(f"   Total post-2020 unmapped: {len(unmapped_post_2020)}")
if len(unmapped_post_2020) > 0:
    # Show sample of unmapped
    sample_unmapped = list(unmapped_post_2020)[:5]
    print(f"\n   Sample unmapped Arcadia IDs (first 5):")
    for arc_id in sample_unmapped:
        row = df_arcadia[df_arcadia['ID'] == arc_id].iloc[0]
        print(f"   - ID {arc_id}: {row['Target Company']} "
              f"(Ann: {row['Announcement date*']}, Size: ${row['Transaction Size*, $M']}M)")

# 8. Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print(f"\nKEY FINDINGS:")
print(f"   1. Total Arcadia transactions: {len(df_arcadia)}")
print(f"   2. Pre-2020 transactions: {len(df_arcadia[df_arcadia['date_category'] == 'pre-2020'])} "
      f"({len(df_arcadia[df_arcadia['date_category'] == 'pre-2020'])/len(df_arcadia)*100:.1f}%)")
print(f"   3. Post-2020 transactions: {len(df_arcadia[df_arcadia['date_category'] == 'post-2020'])} "
      f"({len(df_arcadia[df_arcadia['date_category'] == 'post-2020'])/len(df_arcadia)*100:.1f}%)")
print(f"   4. Overall mapping coverage: {len(mapped_in_arcadia)/len(df_arcadia)*100:.1f}%")

post_2020_coverage = len(post_2020_ids.intersection(mapped_ids))/len(post_2020_ids)*100 if len(post_2020_ids) > 0 else 0
print(f"   5. Post-2020 mapping coverage: {post_2020_coverage:.1f}%")

pre_2020_data = df_arcadia[df_arcadia['date_category'] == 'pre-2020']
if len(pre_2020_data) > 0:
    pre_2020_ids = set(pre_2020_data['ID'].values)
    pre_2020_coverage = len(pre_2020_ids.intersection(mapped_ids))/len(pre_2020_ids)*100
    print(f"   6. Pre-2020 mapping coverage: {pre_2020_coverage:.1f}% (should be ~0%)")

print("\n" + "=" * 80)