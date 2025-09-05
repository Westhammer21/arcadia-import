import pandas as pd
from datetime import datetime

def update_to_be_created_companies():
    print("=" * 80)
    print("UPDATING TO BE CREATED COMPANIES WITH ARCADIA DATA")
    print("=" * 80)
    print()
    
    # Load files
    print("[INFO] Loading files...")
    unmapped_df = pd.read_csv('output/arcadia_company_unmapped.csv')
    arcadia_df = pd.read_csv('src/company-names-arcadia.csv')
    
    # Find TO BE CREATED companies that now have IDs
    to_be_created_with_ids = unmapped_df[
        (unmapped_df['status'] == 'TO BE CREATED') & 
        (unmapped_df['id'].notna())
    ].copy()
    
    print(f"[INFO] Found {len(to_be_created_with_ids)} TO BE CREATED companies with IDs")
    print()
    
    if len(to_be_created_with_ids) == 0:
        print("[INFO] No TO BE CREATED companies with IDs found. Nothing to update.")
        return
    
    updates_made = []
    
    for idx in to_be_created_with_ids.index:
        company_id = unmapped_df.loc[idx, 'id']
        original_name = unmapped_df.loc[idx, 'name']
        ig_id = unmapped_df.loc[idx, 'IG_ID']
        
        # Find the company in Arcadia database
        arc_match = arcadia_df[arcadia_df['id'] == company_id]
        
        if not arc_match.empty:
            arc_row = arc_match.iloc[0]
            
            # Update with Arcadia data
            unmapped_df.loc[idx, 'name'] = arc_row['name']
            unmapped_df.loc[idx, 'also_known_as'] = arc_row.get('also_known_as', '')
            unmapped_df.loc[idx, 'aliases'] = arc_row.get('aliases', '')
            unmapped_df.loc[idx, 'type'] = arc_row.get('type', '')
            unmapped_df.loc[idx, 'founded'] = arc_row.get('founded', '')
            unmapped_df.loc[idx, 'hq_country'] = arc_row.get('hq_country', '')
            unmapped_df.loc[idx, 'hq_region'] = arc_row.get('hq_region', '')
            unmapped_df.loc[idx, 'ownership'] = arc_row.get('ownership', '')
            unmapped_df.loc[idx, 'sector'] = arc_row.get('sector', '')
            unmapped_df.loc[idx, 'segment'] = arc_row.get('segment', '')
            unmapped_df.loc[idx, 'features'] = arc_row.get('features', '')
            unmapped_df.loc[idx, 'specialization'] = arc_row.get('specialization', '')
            unmapped_df.loc[idx, 'aum'] = arc_row.get('aum', '')
            unmapped_df.loc[idx, 'parent_company'] = arc_row.get('parent_company', '')
            unmapped_df.loc[idx, 'transactions_count'] = arc_row.get('transactions_count', '')
            unmapped_df.loc[idx, 'was_added'] = arc_row.get('was_added', '')
            unmapped_df.loc[idx, 'created_by'] = arc_row.get('created_by', '')
            unmapped_df.loc[idx, 'was_changed'] = arc_row.get('was_changed', '')
            unmapped_df.loc[idx, 'modified_by'] = arc_row.get('modified_by', '')
            unmapped_df.loc[idx, 'search_index'] = arc_row.get('search_index', '')
            
            # Update status to MATCHED since it now has an ID
            unmapped_df.loc[idx, 'status'] = 'MATCHED'
            
            updates_made.append({
                'original_name': original_name,
                'arcadia_name': arc_row['name'],
                'id': int(company_id),
                'ig_id': ig_id
            })
            
            print(f"[OK] Updated: {original_name}")
            print(f"     -> Arcadia Name: {arc_row['name']}")
            print(f"     -> ID: {int(company_id)}")
            print(f"     -> Status: TO BE CREATED -> MATCHED")
            print()
        else:
            print(f"[WARNING] ID {int(company_id)} not found in Arcadia database for {original_name}")
            print()
    
    # Save the updated file
    try:
        unmapped_df.to_csv('output/arcadia_company_unmapped.csv', index=False)
        print(f"[OK] Updated file saved to output/arcadia_company_unmapped.csv")
    except PermissionError:
        # Save to a temporary file if the main file is locked
        temp_file = 'output/arcadia_company_unmapped_updated.csv'
        unmapped_df.to_csv(temp_file, index=False)
        print(f"[WARNING] Main file is locked. Saved to: {temp_file}")
        print(f"[INFO] Please close the file in Excel and rename {temp_file} to arcadia_company_unmapped.csv")
    print()
    
    # Summary
    print("=" * 80)
    print("UPDATE SUMMARY")
    print("=" * 80)
    print()
    print(f"Total companies updated: {len(updates_made)}")
    
    if updates_made:
        print("\nUpdated companies:")
        print("-" * 50)
        for update in updates_made:
            print(f"  {update['original_name']}")
            print(f"    -> {update['arcadia_name']} (ID: {update['id']})")
    
    # Check final statistics
    print()
    print("FINAL STATISTICS:")
    print("-" * 50)
    
    total_companies = len(unmapped_df)
    with_ids = unmapped_df['id'].notna().sum()
    without_ids = unmapped_df['id'].isna().sum()
    
    print(f"Total companies: {total_companies}")
    print(f"Companies with IDs: {with_ids} ({with_ids/total_companies*100:.1f}%)")
    print(f"Companies without IDs: {without_ids} ({without_ids/total_companies*100:.1f}%)")
    
    # Status breakdown for companies without IDs
    no_id_df = unmapped_df[unmapped_df['id'].isna()]
    if len(no_id_df) > 0:
        print("\nCompanies without IDs by status:")
        for status, count in no_id_df['status'].value_counts().items():
            print(f"  {status}: {count}")
    
    print()
    print("[SUCCESS] All updates completed!")

if __name__ == "__main__":
    update_to_be_created_companies()