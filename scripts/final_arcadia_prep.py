import pandas as pd

# Load the prepared file
df = pd.read_csv('output/arcadia_company_unmapped_IMPORT_READY.csv')

# Fix the "IS INCOMPLETE" (with space) to "IS_INCOMPLETE" (with underscore)
df['status'] = df['status'].str.replace('IS INCOMPLETE', 'IS_INCOMPLETE')

# Save the corrected file
df.to_csv('output/arcadia_company_unmapped_IMPORT_READY.csv', index=False)

print("Fixed status values:")
print(df['status'].value_counts())
print("\n✅ File is now fully Arcadia-compliant!")