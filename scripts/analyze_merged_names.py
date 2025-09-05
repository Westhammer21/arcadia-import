"""
Analyze exact names that were merged to show matching details
"""

import pandas as pd

# Load both original and merged data
original_df = pd.read_csv('output/arcadia_company_cards_deduplicated.csv')
merged_df = pd.read_csv('output/arcadia_company_cards_merged.csv')

print("Analyzing merged company names...")
print("=" * 80)

# Find companies that were merged (appear multiple times in original)
name_counts = original_df['name'].value_counts()
merged_companies = name_counts[name_counts > 1].to_dict()

# Create detailed comparison
comparison_data = []

for company_name, count in sorted(merged_companies.items()):
    # Get all original records for this company
    original_records = original_df[original_df['name'] == company_name]
    
    # Get merged record
    merged_record = merged_df[merged_df['name'] == company_name]
    
    if len(merged_record) > 0:
        merged_ig = str(merged_record.iloc[0]['IG_ID']) if 'IG_ID' in merged_record.columns else ''
        merged_role = str(merged_record.iloc[0].get('ig_role', merged_record.iloc[0].get('investor_role', '')))
        
        # Count IGs in merged record
        ig_count = len([x for x in merged_ig.split(', ') if x and x != 'nan'])
        
        comparison_data.append({
            'Company': company_name,
            'Original_Records': count,
            'Merged_IGs': ig_count,
            'Status': 'Merged'
        })
        
        # Show details for each original record
        print(f"\n[{company_name}]")
        print(f"  Original records: {count}")
        for idx, row in original_records.iterrows():
            ig_id = row.get('IG_ID', '')
            role = row.get('investor_role', '')
            status = row.get('status', '')
            print(f"    - IG: {ig_id}, Role: {role}, Status: {status}")
        print(f"  Merged result:")
        print(f"    - IGs: {merged_ig}")
        print(f"    - Roles: {merged_role}")

# Save detailed comparison
comparison_df = pd.DataFrame(comparison_data)
comparison_df.to_csv('output/merged_names_comparison.csv', index=False)

print("\n" + "=" * 80)
print(f"Total companies merged: {len(merged_companies)}")
print(f"Original total records: {sum(merged_companies.values())}")
print(f"Records after merge: {len(merged_companies)}")
print(f"Records eliminated: {sum(merged_companies.values()) - len(merged_companies)}")

print("\nDetailed comparison saved to: output/merged_names_comparison.csv")