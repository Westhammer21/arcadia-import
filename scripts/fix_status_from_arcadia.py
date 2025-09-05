import pandas as pd

def fix_status_from_arcadia():
    print("=" * 80)
    print("FIXING STATUS VALUES FROM ARCADIA DATABASE")
    print("=" * 80)
    print()
    
    # Load files
    print("[INFO] Loading files...")
    unmapped_df = pd.read_csv('output/arcadia_company_unmapped.csv')
    arcadia_df = pd.read_csv('src/company-names-arcadia.csv')
    
    # Find all companies with status "MATCHED" (incorrectly set)
    matched_companies = unmapped_df[unmapped_df['status'] == 'MATCHED'].copy()
    
    print(f"[INFO] Found {len(matched_companies)} companies with 'MATCHED' status to fix")
    print()
    
    updates_made = 0
    
    for idx in matched_companies.index:
        company_id = unmapped_df.loc[idx, 'id']
        company_name = unmapped_df.loc[idx, 'name']
        
        if pd.notna(company_id):
            # Find the company in Arcadia database
            arc_match = arcadia_df[arcadia_df['id'] == company_id]
            
            if not arc_match.empty:
                arc_row = arc_match.iloc[0]
                correct_status = arc_row.get('status', 'ENABLED')  # Default to ENABLED if status is missing
                
                # Update the status
                old_status = unmapped_df.loc[idx, 'status']
                unmapped_df.loc[idx, 'status'] = correct_status
                
                if old_status != correct_status:
                    updates_made += 1
                    print(f"[OK] Fixed status for {company_name}")
                    print(f"     ID: {int(company_id)}")
                    print(f"     Status: MATCHED -> {correct_status}")
                    print()
    
    # Also check for any other companies with IDs to ensure they have correct status
    print("[INFO] Checking all companies with IDs for correct status...")
    all_with_ids = unmapped_df[unmapped_df['id'].notna()].copy()
    
    additional_fixes = 0
    for idx in all_with_ids.index:
        company_id = unmapped_df.loc[idx, 'id']
        current_status = unmapped_df.loc[idx, 'status']
        
        # Skip if already processed above
        if current_status == 'MATCHED':
            continue
            
        # Find in Arcadia
        arc_match = arcadia_df[arcadia_df['id'] == company_id]
        if not arc_match.empty:
            arc_row = arc_match.iloc[0]
            correct_status = arc_row.get('status', 'ENABLED')
            
            # Check if status needs updating
            if current_status != correct_status and current_status not in ['ENABLED', 'IS INCOMPLETE', 'IMPORTED']:
                unmapped_df.loc[idx, 'status'] = correct_status
                additional_fixes += 1
                print(f"[OK] Also fixed: {unmapped_df.loc[idx, 'name']} ({current_status} -> {correct_status})")
    
    # Save the updated file
    try:
        unmapped_df.to_csv('output/arcadia_company_unmapped.csv', index=False)
        print(f"\n[OK] Updated file saved to output/arcadia_company_unmapped.csv")
    except PermissionError:
        temp_file = 'output/arcadia_company_unmapped_status_fixed.csv'
        unmapped_df.to_csv(temp_file, index=False)
        print(f"\n[WARNING] Main file is locked. Saved to: {temp_file}")
        print(f"[INFO] Please close the file in Excel and rename {temp_file} to arcadia_company_unmapped.csv")
    
    print()
    print("=" * 80)
    print("STATUS FIX SUMMARY")
    print("=" * 80)
    print()
    print(f"Total 'MATCHED' statuses fixed: {updates_made}")
    print(f"Additional status corrections: {additional_fixes}")
    print(f"Total fixes applied: {updates_made + additional_fixes}")
    
    # Show final status distribution
    print("\nFinal status distribution:")
    status_counts = unmapped_df['status'].value_counts()
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    print()
    print("[SUCCESS] All status values corrected from Arcadia database!")

if __name__ == "__main__":
    fix_status_from_arcadia()