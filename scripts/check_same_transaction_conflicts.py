"""
Check if any company appears as both investor and target in the same transaction ID
"""

import pandas as pd

# Load the merged data
df = pd.read_csv('output/arcadia_company_cards_merged.csv')

print("Analyzing for companies appearing as both investor and target in SAME transaction...")
print("=" * 80)

conflicts = []

for _, row in df.iterrows():
    company_name = row['name']
    ig_ids = str(row.get('IG_ID', '')).split(', ') if pd.notna(row.get('IG_ID')) else []
    roles = str(row.get('ig_role', '')).split(', ') if pd.notna(row.get('ig_role')) else []
    
    if len(ig_ids) != len(roles):
        print(f"[WARNING] Mismatch in {company_name}: {len(ig_ids)} IGs vs {len(roles)} roles")
        continue
    
    # Check each IG_ID
    ig_role_map = {}
    for ig_id, role in zip(ig_ids, roles):
        if ig_id and ig_id != 'nan':
            # Normalize role
            normalized_role = 'target' if role.lower() == 'target' else 'investor'
            
            if ig_id not in ig_role_map:
                ig_role_map[ig_id] = set()
            ig_role_map[ig_id].add(normalized_role)
    
    # Check for conflicts (same IG with both roles)
    for ig_id, roles_set in ig_role_map.items():
        if len(roles_set) > 1 and 'target' in roles_set and 'investor' in roles_set:
            conflicts.append({
                'company': company_name,
                'IG_ID': ig_id,
                'roles': list(roles_set)
            })
            print(f"\n[CONFLICT FOUND!]")
            print(f"  Company: {company_name}")
            print(f"  IG_ID: {ig_id}")
            print(f"  Appears as: {', '.join(roles_set)}")

# Also check original data for comparison
print("\n" + "=" * 80)
print("Double-checking with original data...")

original_df = pd.read_csv('output/ig_arc_unmapped_investors_FINAL.csv')

# Group by IG_ID
for ig_id in original_df['IG_ID'].unique():
    if pd.isna(ig_id):
        continue
    
    transaction_data = original_df[original_df['IG_ID'] == ig_id]
    
    # Check if this transaction has both target and investor roles
    target_companies = set(transaction_data[transaction_data['investor_role'] == 'TARGET']['Target name'].unique())
    investor_companies = set(transaction_data[transaction_data['investor_role'] != 'TARGET']['investor_name'].unique())
    
    # Check for overlap
    overlap = target_companies.intersection(investor_companies)
    
    if overlap:
        print(f"\n[POTENTIAL ISSUE in Transaction {ig_id}]")
        print(f"  Companies appearing as BOTH target and investor:")
        for company in overlap:
            print(f"    - {company}")
            target_info = transaction_data[(transaction_data['Target name'] == company) & (transaction_data['investor_role'] == 'TARGET')]
            investor_info = transaction_data[(transaction_data['investor_name'] == company) & (transaction_data['investor_role'] != 'TARGET')]
            print(f"      As target: {len(target_info)} times")
            print(f"      As investor: {len(investor_info)} times")

print("\n" + "=" * 80)
print("FINAL RESULTS:")
print("=" * 80)

if conflicts:
    print(f"[CRITICAL] Found {len(conflicts)} conflicts where a company appears as both")
    print("           investor AND target in the SAME transaction ID!")
    
    # Save conflicts to file
    conflicts_df = pd.DataFrame(conflicts)
    conflicts_df.to_csv('output/same_transaction_conflicts.csv', index=False)
    print("\nConflicts saved to: output/same_transaction_conflicts.csv")
else:
    print("[SUCCESS] No companies found appearing as both investor and target in the same transaction.")
    print("          All dual-role companies participate in DIFFERENT transactions.")

# Additional analysis: Show dual-role companies
print("\n" + "=" * 80)
print("Dual-role companies (appearing in different transactions):")
print("-" * 80)

dual_role_companies = []
for _, row in df.iterrows():
    company_name = row['name']
    roles = str(row.get('ig_role', '')).split(', ') if pd.notna(row.get('ig_role')) else []
    
    has_target = any(r.lower() == 'target' for r in roles)
    has_investor = any(r.lower() in ['lead', 'participant'] for r in roles)
    
    if has_target and has_investor:
        target_count = sum(1 for r in roles if r.lower() == 'target')
        investor_count = len(roles) - target_count
        dual_role_companies.append({
            'Company': company_name,
            'Target Transactions': target_count,
            'Investor Transactions': investor_count
        })

if dual_role_companies:
    dual_df = pd.DataFrame(dual_role_companies)
    print(dual_df.head(10).to_string(index=False))
    print(f"\nTotal dual-role companies: {len(dual_role_companies)}")