import pandas as pd
import numpy as np

print("=" * 80)
print("FINAL DATA VERIFICATION")
print("=" * 80)
print()

# Load both tables
print("[1] Loading tables...")
transactions_df = pd.read_csv('output/ig_arc_unmapped_vF.csv')
companies_df = pd.read_csv('output/arcadia_company_unmapped.csv')

print(f"   Transactions table: {len(transactions_df)} rows")
print(f"   Companies table: {len(companies_df)} rows")
print()

# Check transaction table structure
print("[2] Transaction table structure:")
print(f"   Key columns: IG_ID, Target name, Investors / Buyers")
print(f"   Unique transactions: {len(transactions_df)}")
print()

# Check companies table structure
print("[3] Companies table structure:")
print(f"   Key columns: name, id, status, IG_ID, ig_role")
print()

# Verify IG_ID linkage
print("[4] IG_ID Linkage Verification:")
print("-" * 50)

# Get all IG_IDs from companies table
all_ig_ids_in_companies = []
for ig_id_str in companies_df['IG_ID'].dropna():
    if pd.notna(ig_id_str) and str(ig_id_str).strip():
        # Split by comma and clean
        ids = [id.strip() for id in str(ig_id_str).split(',')]
        all_ig_ids_in_companies.extend(ids)

unique_ig_ids_in_companies = set(all_ig_ids_in_companies)
print(f"   Unique IG_IDs referenced in companies table: {len(unique_ig_ids_in_companies)}")

# Get all IG_IDs from transactions table
ig_ids_in_transactions = set(transactions_df['IG_ID'].dropna().astype(str))
print(f"   Unique IG_IDs in transactions table: {len(ig_ids_in_transactions)}")

# Check coverage
missing_in_companies = ig_ids_in_transactions - unique_ig_ids_in_companies
extra_in_companies = unique_ig_ids_in_companies - ig_ids_in_transactions

print(f"   IG_IDs in transactions but not in companies: {len(missing_in_companies)}")
if missing_in_companies:
    print(f"     Missing IDs: {list(missing_in_companies)[:10]}")
    
print(f"   IG_IDs in companies but not in transactions: {len(extra_in_companies)}")
if extra_in_companies:
    print(f"     Extra IDs: {list(extra_in_companies)[:10]}")
print()

# Company status breakdown
print("[5] Company Status Breakdown:")
print("-" * 50)
status_counts = companies_df['status'].value_counts()
total = len(companies_df)
for status, count in status_counts.items():
    pct = count/total*100
    print(f"   {status}: {count} ({pct:.1f}%)")
print(f"   TOTAL: {total}")
print()

# ID assignment status
print("[6] ID Assignment Status:")
print("-" * 50)
with_id = companies_df['id'].notna().sum()
without_id = companies_df['id'].isna().sum()
print(f"   Companies WITH Arcadia ID: {with_id} ({with_id/len(companies_df)*100:.1f}%)")
print(f"   Companies WITHOUT Arcadia ID: {without_id} ({without_id/len(companies_df)*100:.1f}%)")
print()

# Breakdown of companies without IDs
no_id_df = companies_df[companies_df['id'].isna()]
print("   Companies without IDs by status:")
for status in no_id_df['status'].value_counts().index:
    count = (no_id_df['status'] == status).sum()
    print(f"     {status}: {count}")
print()

# Check data integrity
print("[7] Data Integrity Checks:")
print("-" * 50)

# Check for duplicate company names with same ID
companies_with_id = companies_df[companies_df['id'].notna()]
duplicate_id_names = companies_with_id[companies_with_id.duplicated(subset=['name', 'id'], keep=False)]
print(f"   Duplicate (name, id) pairs: {len(duplicate_id_names)}")

# Check for same name different ID
name_groups = companies_with_id.groupby('name')['id'].nunique()
multi_id_names = name_groups[name_groups > 1]
print(f"   Company names with multiple IDs: {len(multi_id_names)}")
if len(multi_id_names) > 0:
    print("   Examples:")
    for name in multi_id_names.index[:3]:
        ids = companies_with_id[companies_with_id['name'] == name]['id'].unique()
        print(f"     '{name}': IDs {list(ids)}")

# Check for companies with multiple IG_IDs (this is expected for merged companies)
multi_ig_companies = companies_df[companies_df['IG_ID'].notna() & companies_df['IG_ID'].str.contains(',', na=False)]
print(f"   Companies with multiple IG_IDs (merged): {len(multi_ig_companies)}")
print()

# Role distribution
print("[8] Company Role Distribution:")
print("-" * 50)
role_counts = companies_df['ig_role'].value_counts()
for role, count in role_counts.items():
    print(f"   {role}: {count}")
print()

# Summary
print("[9] FINAL SUMMARY:")
print("=" * 80)
print(f"[OK] Total unmapped transactions: {len(transactions_df)}")
print(f"[OK] Total unique companies extracted: {len(companies_df)}")
print(f"[OK] Companies successfully matched to Arcadia: {with_id}")
print(f"[OK] Companies still needing Arcadia IDs: {without_id}")
print(f"     - TO BE CREATED (new to Arcadia): {(no_id_df['status'] == 'TO BE CREATED').sum()}")
print(f"     - IMPORTED (existing but unmapped): {(no_id_df['status'] == 'IMPORTED').sum()}")
print()

# Transaction coverage check
print("[10] Transaction Coverage:")
print("-" * 50)
# Count how many transactions have all their companies mapped
transactions_with_all_mapped = 0
transactions_partially_mapped = 0
transactions_unmapped = 0

for _, tx in transactions_df.iterrows():
    tx_id = str(tx['IG_ID'])
    # Find all companies for this transaction
    companies_for_tx = companies_df[companies_df['IG_ID'].notna() & companies_df['IG_ID'].str.contains(tx_id, na=False)]
    
    if len(companies_for_tx) > 0:
        # Check if all have IDs
        if companies_for_tx['id'].notna().all():
            transactions_with_all_mapped += 1
        elif companies_for_tx['id'].notna().any():
            transactions_partially_mapped += 1
        else:
            transactions_unmapped += 1

print(f"   Transactions with all companies mapped: {transactions_with_all_mapped}")
print(f"   Transactions partially mapped: {transactions_partially_mapped}")
print(f"   Transactions with no mapping: {transactions_unmapped}")
print()

# Final verdict
all_ig_ids_covered = len(missing_in_companies) == 0
print("=" * 80)
if all_ig_ids_covered:
    print("[SUCCESS] ALL IG_IDs ARE PROPERLY LINKED BETWEEN TABLES")
    print("[SUCCESS] The tables are complete and ready for use")
else:
    print("[WARNING] Some IG_IDs are not properly linked")
    print("[INFO] This may be expected if some transactions were filtered out")
    
print()
print("FINAL FILES:")
print("  1. output/ig_arc_unmapped_vF.csv - Original unmapped transactions")
print("  2. output/arcadia_company_unmapped.csv - All companies with mapping status")
print("=" * 80)