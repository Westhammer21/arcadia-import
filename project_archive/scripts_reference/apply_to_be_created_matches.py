import pandas as pd
from datetime import datetime

def apply_matches():
    print("=" * 80)
    print("APPLYING TO BE CREATED DUPLICATE MATCHES")
    print("=" * 80)
    print()
    
    # Load files
    print("[INFO] Loading files...")
    unmapped_df = pd.read_csv('output/arcadia_company_unmapped.csv')
    arcadia_df = pd.read_csv('src/company-names-arcadia.csv')
    
    # Define the matches to apply
    matches_to_apply = [
        {'unmapped_name': 'Apex Capital Partners', 'arcadia_id': 3575, 'ig_id': '2215'},
        {'unmapped_name': 'Aleph VC', 'arcadia_id': 9956, 'ig_id': '4143'},
        {'unmapped_name': 'Handelsbanken Fonder', 'arcadia_id': 8137, 'ig_id': '3023'},
        {'unmapped_name': 'IDEO CoLab', 'arcadia_id': 8275, 'ig_id': '1254'},
        {'unmapped_name': 'Lazarte Brothers', 'arcadia_id': 10755, 'ig_id': '453'},
        {'unmapped_name': 'Meta (NASDAQ: META)', 'arcadia_id': 8531, 'ig_id': '2391'},
        {'unmapped_name': 'NTT DOCOMO Ventures', 'arcadia_id': 3545, 'ig_id': '3230'},
        {'unmapped_name': 'Third Wave', 'arcadia_id': 10497, 'ig_id': '3841'}
    ]
    
    updates_applied = []
    
    print("[INFO] Applying matches...")
    print()
    
    for match in matches_to_apply:
        # Find the row in unmapped_df
        mask = (unmapped_df['name'] == match['unmapped_name'])
        
        if mask.any():
            idx = unmapped_df.index[mask].tolist()[0]
            
            # Get the Arcadia name
            arc_row = arcadia_df[arcadia_df['id'] == match['arcadia_id']]
            if not arc_row.empty:
                arcadia_name = arc_row.iloc[0]['name']
                
                # Store original values for reporting
                original_id = unmapped_df.loc[idx, 'id']
                original_status = unmapped_df.loc[idx, 'status']
                
                # Apply updates
                unmapped_df.loc[idx, 'id'] = match['arcadia_id']
                unmapped_df.loc[idx, 'name'] = arcadia_name  # Update to Arcadia name
                unmapped_df.loc[idx, 'status'] = 'MATCHED'
                
                updates_applied.append({
                    'original_name': match['unmapped_name'],
                    'arcadia_name': arcadia_name,
                    'arcadia_id': match['arcadia_id'],
                    'ig_id': match['ig_id'],
                    'original_status': original_status
                })
                
                print(f"[OK] Updated: {match['unmapped_name']}")
                print(f"     -> ID: {match['arcadia_id']}")
                print(f"     -> Name: {arcadia_name}")
                print(f"     -> Status: TO BE CREATED -> MATCHED")
                print()
        else:
            print(f"[WARNING] Could not find '{match['unmapped_name']}' in unmapped file")
    
    # Save updated file
    unmapped_df.to_csv('output/arcadia_company_unmapped.csv', index=False)
    print(f"[OK] Updated file saved to output/arcadia_company_unmapped.csv")
    print()
    
    # Generate summary report
    print("=" * 80)
    print("SUMMARY OF CHANGES")
    print("=" * 80)
    print()
    print(f"Total updates applied: {len(updates_applied)}")
    print()
    
    if updates_applied:
        print("Updated companies:")
        print("-" * 50)
        for update in updates_applied:
            print(f"  {update['original_name']}")
            print(f"    -> Arcadia Name: {update['arcadia_name']}")
            print(f"    -> Arcadia ID: {update['arcadia_id']}")
            print(f"    -> IG_ID: {update['ig_id']}")
            print()
    
    # Check remaining TO BE CREATED companies
    remaining_to_create = unmapped_df[
        (unmapped_df['status'] == 'TO BE CREATED') & 
        (unmapped_df['id'].isna())
    ]
    
    print(f"[INFO] Remaining TO BE CREATED companies without IDs: {len(remaining_to_create)}")
    
    # Check overall statistics
    print()
    print("=" * 80)
    print("OVERALL STATISTICS")
    print("=" * 80)
    print()
    
    total_companies = len(unmapped_df)
    with_ids = unmapped_df['id'].notna().sum()
    without_ids = unmapped_df['id'].isna().sum()
    
    print(f"Total companies: {total_companies}")
    print(f"Companies with IDs: {with_ids}")
    print(f"Companies without IDs: {without_ids}")
    print()
    
    # Status breakdown for companies without IDs
    no_id_df = unmapped_df[unmapped_df['id'].isna()]
    status_counts = no_id_df['status'].value_counts()
    
    print("Companies without IDs by status:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    print()
    print("[OK] All updates completed successfully!")

if __name__ == "__main__":
    apply_matches()