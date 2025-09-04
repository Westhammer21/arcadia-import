import pandas as pd
from datetime import datetime
import numpy as np

print("=" * 80)
print("SAVING ARCADIA COVERAGE ANALYSIS RESULTS")
print("=" * 80)

# 1. Read Arcadia database
print("\n1. Reading Arcadia database...")
arcadia_file = '../src/arcadia_database_2025-09-01.csv'
df_arcadia = pd.read_csv(arcadia_file, sep='\t')
print(f"   Total Arcadia transactions: {len(df_arcadia)}")

# 2. Parse dates
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

# 3. Categorize transactions by date
cutoff_date = datetime(2020, 1, 1)

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

# Extract year
df_arcadia['year'] = df_arcadia['announcement_date_parsed'].apply(
    lambda x: x.year if pd.notna(x) else None
)

# For transactions with no announcement date, try closed date
mask = df_arcadia['year'].isna()
df_arcadia.loc[mask, 'year'] = df_arcadia.loc[mask, 'closed_date_parsed'].apply(
    lambda x: x.year if pd.notna(x) else None
)

# 4. Read mapping file to get mapped Arcadia IDs
print("\n2. Reading mapping file...")
mapping_file = '../output/ig_arc_mapping_full.csv'
df_mapping = pd.read_csv(mapping_file)

# Get mapped Arcadia IDs (non-null ARC_ID values)
mapped_arc_ids = df_mapping[df_mapping['ARC_ID'].notna()]['ARC_ID'].astype(int).unique()
print(f"   Total unique Arcadia IDs in mapping: {len(mapped_arc_ids)}")

# 5. Add mapping status to Arcadia database
df_arcadia['is_mapped'] = df_arcadia['ID'].isin(mapped_arc_ids)

# 6. Create summary statistics
print("\n3. Creating summary statistics...")

# Overall statistics
overall_stats = pd.DataFrame([{
    'Category': 'Overall',
    'Total_Transactions': len(df_arcadia),
    'Mapped_Transactions': df_arcadia['is_mapped'].sum(),
    'Unmapped_Transactions': (~df_arcadia['is_mapped']).sum(),
    'Coverage_Percentage': df_arcadia['is_mapped'].sum() / len(df_arcadia) * 100
}])

# By date category
date_stats = []
for category in ['pre-2020', 'post-2020', 'unknown-date']:
    cat_data = df_arcadia[df_arcadia['date_category'] == category]
    if len(cat_data) > 0:
        date_stats.append({
            'Category': category,
            'Total_Transactions': len(cat_data),
            'Mapped_Transactions': cat_data['is_mapped'].sum(),
            'Unmapped_Transactions': (~cat_data['is_mapped']).sum(),
            'Coverage_Percentage': cat_data['is_mapped'].sum() / len(cat_data) * 100 if len(cat_data) > 0 else 0
        })

df_date_stats = pd.DataFrame(date_stats)

# By year statistics
year_stats = []
for year in range(2020, 2026):
    year_data = df_arcadia[df_arcadia['year'] == year]
    if len(year_data) > 0:
        year_stats.append({
            'Year': year,
            'Total_Transactions': len(year_data),
            'Mapped_Transactions': year_data['is_mapped'].sum(),
            'Unmapped_Transactions': (~year_data['is_mapped']).sum(),
            'Coverage_Percentage': year_data['is_mapped'].sum() / len(year_data) * 100
        })

df_year_stats = pd.DataFrame(year_stats)

# 7. Get unmapped transaction details
unmapped_post_2020 = df_arcadia[(df_arcadia['date_category'] == 'post-2020') & (~df_arcadia['is_mapped'])]
unmapped_details = unmapped_post_2020[['ID', 'Target Company', 'Announcement date*', 'Transaction Size*, $M', 'year']].copy()
unmapped_details.columns = ['Arcadia_ID', 'Target_Company', 'Announcement_Date', 'Transaction_Size_M', 'Year']

# 8. Save all results
print("\n4. Saving results...")

# Save main coverage analysis
output_file = '../output/arcadia_coverage_analysis.csv'
with pd.ExcelWriter(output_file.replace('.csv', '.xlsx'), engine='openpyxl') as writer:
    overall_stats.to_excel(writer, sheet_name='Overall_Coverage', index=False)
    df_date_stats.to_excel(writer, sheet_name='Coverage_by_Period', index=False)
    df_year_stats.to_excel(writer, sheet_name='Coverage_by_Year', index=False)
    unmapped_details.to_excel(writer, sheet_name='Unmapped_Post2020', index=False)
    
print(f"   Saved Excel file: {output_file.replace('.csv', '.xlsx')}")

# Also save summary CSV files
overall_stats.to_csv('../output/arcadia_coverage_summary.csv', index=False)
df_year_stats.to_csv('../output/arcadia_coverage_by_year.csv', index=False)
unmapped_details.to_csv('../output/arcadia_unmapped_post2020.csv', index=False)

print(f"   Saved summary CSV: arcadia_coverage_summary.csv")
print(f"   Saved yearly CSV: arcadia_coverage_by_year.csv")
print(f"   Saved unmapped list: arcadia_unmapped_post2020.csv")

# 9. Print summary
print("\n" + "=" * 80)
print("COVERAGE ANALYSIS SUMMARY")
print("=" * 80)

print(f"\nOVERALL COVERAGE:")
print(f"   Total Arcadia transactions: {len(df_arcadia)}")
print(f"   Mapped to InvestGame: {df_arcadia['is_mapped'].sum()} ({df_arcadia['is_mapped'].sum()/len(df_arcadia)*100:.1f}%)")
print(f"   Unmapped: {(~df_arcadia['is_mapped']).sum()}")

print(f"\nBY PERIOD:")
for _, row in df_date_stats.iterrows():
    print(f"   {row['Category']}: {row['Mapped_Transactions']}/{row['Total_Transactions']} ({row['Coverage_Percentage']:.1f}%)")

print(f"\nBY YEAR (2020+):")
for _, row in df_year_stats.iterrows():
    print(f"   {int(row['Year'])}: {row['Mapped_Transactions']}/{row['Total_Transactions']} ({row['Coverage_Percentage']:.1f}%)")

print(f"\nUNMAPPED POST-2020: {len(unmapped_post_2020)} transactions")

print("\n" + "=" * 80)
print("ALL FILES SAVED SUCCESSFULLY!")
print("=" * 80)