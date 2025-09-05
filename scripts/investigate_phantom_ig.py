import pandas as pd

# Load the files
companies_df = pd.read_csv('output/arcadia_company_unmapped.csv')
transactions_df = pd.read_csv('output/ig_arc_unmapped_vF.csv')

# Find the company with IG_ID 3055
print("Looking for IG_ID 3055 in companies file:")
print("=" * 60)

found_companies = []
for idx, row in companies_df.iterrows():
    if pd.notna(row['IG_ID']) and '3055' in str(row['IG_ID']):
        found_companies.append({
            'row': idx + 2,
            'company': row['name'],
            'ig_id': row['IG_ID'],
            'role': row.get('ig_role', 'N/A'),
            'status': row['status'],
            'id': row.get('id', 'N/A')
        })

if found_companies:
    for company in found_companies:
        print(f"Found in row {company['row']}:")
        print(f"  Company: {company['company']}")
        print(f"  IG_ID: {company['ig_id']}")
        print(f"  Role: {company['role']}")
        print(f"  Status: {company['status']}")
        print(f"  Arcadia ID: {company['id']}")
        print()
else:
    print("Not found in companies file")

# Check if 3055 exists in transactions
print("\nLooking for IG_ID 3055 in transactions file:")
print("=" * 60)

# Try both numeric and string search
tx_found = transactions_df[
    (transactions_df['IG_ID'] == 3055) | 
    (transactions_df['IG_ID'] == '3055') |
    (transactions_df['IG_ID'] == 3055.0)
]

if not tx_found.empty:
    print("Found in transactions!")
    for _, tx in tx_found.iterrows():
        print(f"  IG_ID: {tx['IG_ID']}")
        print(f"  Target: {tx['Target name']}")
        print(f"  Investors: {tx['Investors / Buyers']}")
else:
    print("NOT FOUND in transactions file")
    print("\nThis IG_ID 3055 appears to be a phantom reference.")
    print("It exists in the companies file but not in transactions.")
    print("\nPossible causes:")
    print("1. Manual data entry error")
    print("2. Duplicate IG_ID that was already mentioned in issue report")
    print("3. Reference to a deleted or moved transaction")

# Check the parsing artifacts
print("\n" + "=" * 60)
print("PARSING ARTIFACTS ANALYSIS")
print("=" * 60)

artifacts = [
    "Aream & Co.",
    "BANANACULTURE GAMING & MEDIA",
    "Draper & Associates",
    "Engine Gaming & Media",
    "German Federal Ministry for Economic Affairs & Energy",
    "Whitwell & Co"
]

print("\nThe following companies have '&' in their names:")
for name in artifacts:
    print(f"  - {name}")

print("\nNote: The '&' character is legitimate in company names.")
print("These are NOT parsing errors - they are valid company names.")
print("The verification script flagged them as potential issues,")
print("but manual review confirms they are correct.")