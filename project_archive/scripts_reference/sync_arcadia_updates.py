"""
Sync and update company data with Arcadia database
Critical requirements:
1. Merge companies with same ID
2. Update manually mapped companies 
3. Preserve arc_website, IG_ID, ig_role columns
4. Validate data integrity
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

class ArcadiaSync:
    def __init__(self):
        self.change_log = []
        self.issues = []
        self.stats = {
            'total_companies': 0,
            'manually_mapped': 0,
            'merged_companies': 0,
            'updated_companies': 0,
            'issues_found': 0,
            'companies_without_id': 0
        }
        
    def load_data(self):
        """Load both CSV files"""
        print("[LOAD] Loading data files...")
        
        # Load unmapped companies
        self.unmapped_df = pd.read_csv('output/arcadia_company_unmapped.csv')
        self.original_df = self.unmapped_df.copy()  # Keep original for comparison
        
        # Load Arcadia database
        self.arcadia_df = pd.read_csv('src/company-names-arcadia.csv')
        
        print(f"  - Loaded {len(self.unmapped_df)} unmapped companies")
        print(f"  - Loaded {len(self.arcadia_df)} Arcadia companies")
        
        self.stats['total_companies'] = len(self.unmapped_df)
        
        # Create Arcadia lookup by ID
        self.arcadia_lookup = {}
        for _, row in self.arcadia_df.iterrows():
            self.arcadia_lookup[row['id']] = row.to_dict()
        
        return True
    
    def identify_manually_mapped(self):
        """Find companies that were manually mapped (TO BE CREATED + has ID)"""
        print("\n[IDENTIFY] Finding manually mapped companies...")
        
        manually_mapped = self.unmapped_df[
            (self.unmapped_df['status'] == 'TO BE CREATED') & 
            (self.unmapped_df['id'].notna())
        ]
        
        self.stats['manually_mapped'] = len(manually_mapped)
        print(f"  - Found {len(manually_mapped)} manually mapped companies")
        
        for _, row in manually_mapped.iterrows():
            print(f"    - {row['name']} -> ID {int(row['id'])}")
            
        return manually_mapped
    
    def check_duplicate_ig_ids(self, df):
        """Check for duplicate IG_IDs within same company"""
        print("\n[VALIDATE] Checking for duplicate IG_IDs within companies...")
        
        for idx, row in df.iterrows():
            if pd.notna(row.get('IG_ID')):
                ig_ids = str(row['IG_ID']).split(', ')
                if len(ig_ids) != len(set(ig_ids)):
                    duplicates = [x for x in ig_ids if ig_ids.count(x) > 1]
                    self.issues.append({
                        'type': 'duplicate_ig_id',
                        'company': row['name'],
                        'ig_ids': row['IG_ID'],
                        'duplicates': list(set(duplicates))
                    })
                    print(f"  [WARNING] {row['name']} has duplicate IG_IDs: {set(duplicates)}")
    
    def validate_ig_role_match(self, df):
        """Validate IG_ID count matches ig_role count"""
        print("\n[VALIDATE] Checking IG_ID and ig_role count match...")
        
        mismatches = []
        for idx, row in df.iterrows():
            if pd.notna(row.get('IG_ID')) and pd.notna(row.get('ig_role')):
                ig_ids = str(row['IG_ID']).split(', ')
                roles = str(row['ig_role']).split(', ')
                
                if len(ig_ids) != len(roles):
                    mismatches.append({
                        'company': row['name'],
                        'ig_count': len(ig_ids),
                        'role_count': len(roles),
                        'ig_ids': row['IG_ID'],
                        'roles': row['ig_role']
                    })
                    self.issues.append({
                        'type': 'count_mismatch',
                        'company': row['name'],
                        'ig_count': len(ig_ids),
                        'role_count': len(roles)
                    })
        
        if mismatches:
            print(f"  [ERROR] Found {len(mismatches)} mismatches:")
            for m in mismatches[:5]:
                print(f"    - {m['company']}: {m['ig_count']} IGs vs {m['role_count']} roles")
        else:
            print("  [OK] All IG_ID and ig_role counts match")
        
        return mismatches
    
    def update_from_arcadia(self, row, arcadia_data):
        """Update a row with Arcadia data while preserving special columns"""
        # Preserve special columns
        preserved = {
            'arc_website': row.get('arc_website'),
            'IG_ID': row.get('IG_ID'),
            'ig_role': row.get('ig_role')
        }
        
        # Update with Arcadia data
        arcadia_columns = [
            'id', 'status', 'name', 'also_known_as', 'aliases', 'type',
            'founded', 'hq_country', 'hq_region', 'ownership', 'sector',
            'segment', 'features', 'specialization', 'aum', 'parent_company',
            'transactions_count', 'was_added', 'created_by', 'was_changed',
            'modified_by', 'search_index'
        ]
        
        updated = row.copy()
        for col in arcadia_columns:
            if col in arcadia_data:
                updated[col] = arcadia_data[col]
        
        # Restore preserved columns
        for col, val in preserved.items():
            updated[col] = val
        
        return updated
    
    def merge_companies_by_id(self):
        """Merge companies with the same ID"""
        print("\n[MERGE] Merging companies with same IDs...")
        
        # Group by ID (only for companies with IDs)
        id_groups = self.unmapped_df[self.unmapped_df['id'].notna()].groupby('id')
        
        merged_rows = []
        companies_to_remove = []
        
        for arc_id, group in id_groups:
            if len(group) > 1:
                print(f"\n  Merging ID {int(arc_id)} ({len(group)} entries):")
                
                # Get Arcadia data for this ID
                if arc_id in self.arcadia_lookup:
                    arcadia_data = self.arcadia_lookup[arc_id]
                    
                    # Collect all IG_IDs and roles maintaining order
                    all_ig_ids = []
                    all_roles = []
                    
                    for _, row in group.iterrows():
                        print(f"    - {row['name']}: IG_ID={row.get('IG_ID', 'None')}")
                        
                        if pd.notna(row.get('IG_ID')):
                            ig_ids = str(row['IG_ID']).split(', ')
                            roles = str(row['ig_role']).split(', ') if pd.notna(row.get('ig_role')) else []
                            
                            all_ig_ids.extend(ig_ids)
                            all_roles.extend(roles)
                    
                    # Create merged entry using Arcadia name
                    merged = self.update_from_arcadia(group.iloc[0], arcadia_data)
                    merged['name'] = arcadia_data['name']  # Use official Arcadia name
                    
                    # Concatenate IG_IDs and roles
                    if all_ig_ids:
                        merged['IG_ID'] = ', '.join(all_ig_ids)
                    if all_roles:
                        merged['ig_role'] = ', '.join(all_roles)
                    
                    # Preserve arc_website if any entry has it
                    for _, row in group.iterrows():
                        if pd.notna(row.get('arc_website')) and str(row['arc_website']).strip():
                            merged['arc_website'] = row['arc_website']
                            break
                    
                    print(f"    -> Merged as: {merged['name']} with {len(all_ig_ids)} IG_IDs")
                    
                    merged_rows.append(merged)
                    companies_to_remove.extend(group.index.tolist())
                    self.stats['merged_companies'] += 1
                    
                    # Log the merge
                    self.change_log.append({
                        'action': 'merge',
                        'id': arc_id,
                        'original_names': group['name'].tolist(),
                        'new_name': merged['name'],
                        'ig_ids': merged.get('IG_ID', '')
                    })
                else:
                    self.issues.append({
                        'type': 'missing_arcadia_id',
                        'id': arc_id,
                        'companies': group['name'].tolist()
                    })
                    print(f"    [ERROR] ID {arc_id} not found in Arcadia database")
        
        # Remove original rows and add merged ones
        if companies_to_remove:
            self.unmapped_df = self.unmapped_df.drop(companies_to_remove)
            self.unmapped_df = pd.concat([self.unmapped_df, pd.DataFrame(merged_rows)], ignore_index=True)
            print(f"\n  Total merges completed: {self.stats['merged_companies']}")
    
    def update_all_with_ids(self):
        """Update all companies that have IDs with latest Arcadia data"""
        print("\n[UPDATE] Refreshing all companies with IDs...")
        
        companies_with_ids = self.unmapped_df[self.unmapped_df['id'].notna()]
        updated_count = 0
        
        for idx, row in companies_with_ids.iterrows():
            arc_id = row['id']
            
            if arc_id in self.arcadia_lookup:
                arcadia_data = self.arcadia_lookup[arc_id]
                
                # Check if update needed
                old_status = row['status']
                old_name = row['name']
                
                # Update row
                updated = self.update_from_arcadia(row, arcadia_data)
                
                # Update in dataframe
                for col in updated.index:
                    self.unmapped_df.at[idx, col] = updated[col]
                
                # Log if changed
                if old_status != updated['status'] or old_name != updated['name']:
                    updated_count += 1
                    self.change_log.append({
                        'action': 'update',
                        'id': arc_id,
                        'old_name': old_name,
                        'new_name': updated['name'],
                        'old_status': old_status,
                        'new_status': updated['status']
                    })
                    
                    if old_name != updated['name']:
                        print(f"  - Updated name: {old_name} -> {updated['name']}")
            else:
                self.issues.append({
                    'type': 'id_not_in_arcadia',
                    'id': arc_id,
                    'company': row['name']
                })
                print(f"  [ERROR] ID {int(arc_id)} not found in Arcadia for {row['name']}")
        
        self.stats['updated_companies'] = updated_count
        print(f"  - Total updates: {updated_count}")
    
    def final_validation(self):
        """Perform final validation checks"""
        print("\n[FINAL VALIDATION]")
        
        # Check for duplicate IG_IDs
        self.check_duplicate_ig_ids(self.unmapped_df)
        
        # Validate IG_ID and role counts
        self.validate_ig_role_match(self.unmapped_df)
        
        # Count companies without IDs
        self.stats['companies_without_id'] = self.unmapped_df['id'].isna().sum()
        self.stats['issues_found'] = len(self.issues)
        
        print(f"\n  Summary:")
        print(f"    - Companies without ID: {self.stats['companies_without_id']}")
        print(f"    - Total issues found: {self.stats['issues_found']}")
    
    def save_results(self):
        """Save updated data and reports"""
        print("\n[SAVE] Saving results...")
        
        # Save updated companies
        self.unmapped_df.to_csv('output/arcadia_company_unmapped.csv', index=False, encoding='utf-8')
        print(f"  - Updated file saved: output/arcadia_company_unmapped.csv")
        
        # Save change log
        if self.change_log:
            with open('output/sync_change_log.json', 'w') as f:
                json.dump(self.change_log, f, indent=2, default=str)
            print(f"  - Change log saved: output/sync_change_log.json")
        
        # Save issues
        if self.issues:
            with open('output/sync_issues.json', 'w') as f:
                json.dump(self.issues, f, indent=2, default=str)
            print(f"  - Issues saved: output/sync_issues.json")
        
        # Generate summary report
        self.generate_report()
    
    def generate_report(self):
        """Generate detailed markdown report"""
        report = f"""# Arcadia Sync Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Statistics
- **Total Companies**: {self.stats['total_companies']:,}
- **Manually Mapped**: {self.stats['manually_mapped']}
- **Companies Merged**: {self.stats['merged_companies']}
- **Companies Updated**: {self.stats['updated_companies']}
- **Issues Found**: {self.stats['issues_found']}
- **Companies Without ID**: {self.stats['companies_without_id']}

## Companies Still Without IDs

"""
        # List companies without IDs
        no_id = self.unmapped_df[self.unmapped_df['id'].isna()]
        
        # Group by status
        for status in no_id['status'].unique():
            status_companies = no_id[no_id['status'] == status]
            report += f"### {status} ({len(status_companies)} companies)\n\n"
            
            for _, row in status_companies.head(20).iterrows():
                report += f"- {row['name']}\n"
            
            if len(status_companies) > 20:
                report += f"- ... and {len(status_companies) - 20} more\n"
            report += "\n"
        
        # Add issues section
        if self.issues:
            report += "## Issues Found\n\n"
            
            issue_types = {}
            for issue in self.issues:
                issue_type = issue['type']
                if issue_type not in issue_types:
                    issue_types[issue_type] = []
                issue_types[issue_type].append(issue)
            
            for issue_type, issues in issue_types.items():
                report += f"### {issue_type.replace('_', ' ').title()} ({len(issues)} issues)\n\n"
                
                for issue in issues[:5]:
                    if issue_type == 'duplicate_ig_id':
                        report += f"- {issue['company']}: Duplicate IGs {issue['duplicates']}\n"
                    elif issue_type == 'count_mismatch':
                        report += f"- {issue['company']}: {issue['ig_count']} IGs vs {issue['role_count']} roles\n"
                    elif issue_type == 'id_not_in_arcadia':
                        report += f"- {issue['company']} (ID: {issue['id']})\n"
                    else:
                        report += f"- {issue}\n"
                
                if len(issues) > 5:
                    report += f"- ... and {len(issues) - 5} more\n"
                report += "\n"
        
        # Add change log summary
        if self.change_log:
            report += f"## Changes Applied\n\n"
            report += f"Total changes: {len(self.change_log)}\n\n"
            
            merges = [c for c in self.change_log if c['action'] == 'merge']
            updates = [c for c in self.change_log if c['action'] == 'update']
            
            if merges:
                report += f"### Merges ({len(merges)})\n\n"
                for merge in merges[:10]:
                    report += f"- {', '.join(merge['original_names'])} -> {merge['new_name']}\n"
                report += "\n"
            
            if updates:
                report += f"### Updates ({len(updates)})\n\n"
                for update in updates[:10]:
                    if update['old_name'] != update['new_name']:
                        report += f"- Name: {update['old_name']} -> {update['new_name']}\n"
                    if update['old_status'] != update['new_status']:
                        report += f"- Status: {update['company']}: {update['old_status']} -> {update['new_status']}\n"
                report += "\n"
        
        # Save report
        with open('docs/arcadia_sync_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"  - Report saved: docs/arcadia_sync_report.md")
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"SYNC COMPLETE")
        print(f"{'='*60}")
        print(f"Companies without ID: {self.stats['companies_without_id']}")
        print(f"Issues requiring attention: {self.stats['issues_found']}")

def main():
    print("[START] Arcadia Sync Process")
    print("="*60)
    
    syncer = ArcadiaSync()
    
    # Load data
    syncer.load_data()
    
    # Find manually mapped companies
    syncer.identify_manually_mapped()
    
    # Merge companies with same IDs
    syncer.merge_companies_by_id()
    
    # Update all companies with IDs
    syncer.update_all_with_ids()
    
    # Final validation
    syncer.final_validation()
    
    # Save everything
    syncer.save_results()

if __name__ == "__main__":
    main()