import pandas as pd
from datetime import datetime

def prepare_for_arcadia_import():
    """
    Fix all data issues to make the file Arcadia-import ready
    """
    print("=" * 80)
    print("PREPARING FILE FOR ARCADIA IMPORT")
    print("=" * 80)
    print()
    
    # Load the file
    df = pd.read_csv('output/arcadia_company_unmapped.csv')
    print(f"[INFO] Loaded {len(df)} companies")
    
    issues_fixed = []
    
    # 1. Fix invalid status values
    print("\n[1] Fixing Status Values...")
    to_be_created_count = (df['status'] == 'TO BE CREATED').sum()
    if to_be_created_count > 0:
        # Companies without IDs that need to be created should be IMPORTED
        # This signals to Arcadia they are new external companies
        df.loc[df['status'] == 'TO BE CREATED', 'status'] = 'IMPORTED'
        issues_fixed.append(f"Changed {to_be_created_count} 'TO BE CREATED' to 'IMPORTED'")
        print(f"   [OK] Fixed {to_be_created_count} invalid status values")
    
    # 2. Fix invalid company types
    print("\n[2] Fixing Company Types...")
    
    # Fix TestType entries
    testtype_count = (df['type'] == 'TestType').sum()
    if testtype_count > 0:
        # Default TestType to Strategic / CVC
        df.loc[df['type'] == 'TestType', 'type'] = 'Strategic / CVC'
        issues_fixed.append(f"Changed {testtype_count} 'TestType' to 'Strategic / CVC'")
        print(f"   [OK] Fixed {testtype_count} TestType entries")
    
    # Fix Investor type
    investor_count = (df['type'] == 'Investor').sum()
    if investor_count > 0:
        # Map Investor to appropriate VC type
        df.loc[df['type'] == 'Investor', 'type'] = 'Venture Capital & Accelerators'
        issues_fixed.append(f"Changed {investor_count} 'Investor' to 'Venture Capital & Accelerators'")
        print(f"   [OK] Fixed {investor_count} Investor entries")
    
    # 3. Fix country data
    print("\n[3] Fixing Country Data...")
    
    # Fix notenoughinformation country
    noinfo_country = (df['hq_country'] == 'notenoughinformation').sum()
    if noinfo_country > 0:
        df.loc[df['hq_country'] == 'notenoughinformation', 'hq_country'] = 'XX'
        df.loc[df['hq_country'] == 'XX', 'hq_region'] = 'Unknown'
        issues_fixed.append(f"Changed {noinfo_country} countries from 'notenoughinformation' to 'XX'")
        print(f"   [OK] Fixed {noinfo_country} invalid country codes")
    
    # 4. Handle companies without IDs
    print("\n[4] Handling Missing IDs...")
    no_id_count = df['id'].isna().sum()
    if no_id_count > 0:
        # These should remain empty - Arcadia will assign IDs on import
        # But ensure their status is appropriate
        df.loc[df['id'].isna() & (df['status'] == 'ENABLED'), 'status'] = 'IMPORTED'
        print(f"   [INFO] {no_id_count} companies without IDs marked for new creation")
        issues_fixed.append(f"Marked {no_id_count} companies without IDs as IMPORTED")
    
    # 5. Clean up placeholder years
    print("\n[5] Reviewing Founded Years...")
    year_1800 = (df['founded'] == 1800).sum()
    if year_1800 > 0:
        # Mark these as incomplete if they have placeholder year
        df.loc[(df['founded'] == 1800) & (df['status'] != 'IS_INCOMPLETE'), 'status'] = 'IS_INCOMPLETE'
        print(f"   [INFO] {year_1800} companies with placeholder year 1800")
        issues_fixed.append(f"Marked companies with year 1800 as IS_INCOMPLETE")
    
    # 6. Validate final data
    print("\n[6] Final Validation...")
    
    # Check all status values are valid
    valid_statuses = ['ENABLED', 'DISABLED', 'TO_DELETE', 'IMPORTED', 'IS_INCOMPLETE']
    invalid_statuses = ~df['status'].isin(valid_statuses)
    if invalid_statuses.any():
        print(f"   [WARNING] Still have invalid statuses: {df[invalid_statuses]['status'].unique()}")
    else:
        print("   [OK] All status values are valid")
    
    # Check all types are valid
    valid_types = ['Strategic / CVC', 'Venture Capital & Accelerators', 
                   'Private Equity & Inst.', 'Other']
    invalid_types = ~df['type'].isin(valid_types)
    if invalid_types.any():
        print(f"   [WARNING] Still have invalid types: {df[invalid_types]['type'].unique()}")
    else:
        print("   [OK] All company types are valid")
    
    # Save cleaned file
    output_file = 'output/arcadia_company_unmapped_IMPORT_READY.csv'
    df.to_csv(output_file, index=False)
    print(f"\n[OK] Saved import-ready file to: {output_file}")
    
    # Generate summary report
    print("\n" + "=" * 80)
    print("IMPORT PREPARATION SUMMARY")
    print("=" * 80)
    print()
    print(f"Total Companies: {len(df)}")
    print(f"Issues Fixed: {len(issues_fixed)}")
    print()
    print("Fixes Applied:")
    for fix in issues_fixed:
        print(f"  - {fix}")
    
    print("\nFinal Statistics:")
    print(f"  Companies with IDs: {df['id'].notna().sum()} ({df['id'].notna().sum()/len(df)*100:.1f}%)")
    print(f"  Companies without IDs: {df['id'].isna().sum()} ({df['id'].isna().sum()/len(df)*100:.1f}%)")
    
    print("\nStatus Distribution:")
    for status, count in df['status'].value_counts().items():
        print(f"  {status}: {count}")
    
    print("\nType Distribution:")
    for type_val, count in df['type'].value_counts().items():
        print(f"  {type_val}: {count}")
    
    print("\n" + "=" * 80)
    print("FILE IS NOW READY FOR ARCADIA IMPORT")
    print("=" * 80)
    print()
    print(f"Import file: {output_file}")
    print("\nIT Specialist Instructions:")
    print("1. Use the file: output/arcadia_company_unmapped_IMPORT_READY.csv")
    print("2. Companies with IDs should UPDATE existing records")
    print("3. Companies without IDs should CREATE new records") 
    print("4. Status 'IMPORTED' indicates externally sourced companies")
    print("5. Status 'IS_INCOMPLETE' indicates data quality issues to review")

if __name__ == "__main__":
    prepare_for_arcadia_import()