import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime
import json

class ComprehensiveIGIDVerification:
    def __init__(self):
        self.companies_df = None
        self.transactions_df = None
        self.issues = defaultdict(list)
        self.statistics = {}
        self.verification_results = {}
        
    def load_data(self):
        """Phase 1: Load and prepare data"""
        print("=" * 80)
        print("COMPREHENSIVE IG_ID VERIFICATION")
        print("=" * 80)
        print()
        print("[PHASE 1] Loading and preparing data...")
        
        try:
            self.companies_df = pd.read_csv('output/arcadia_company_unmapped.csv')
            self.transactions_df = pd.read_csv('output/ig_arc_unmapped_vF.csv')
            
            print(f"  [OK] Loaded companies file: {len(self.companies_df)} records")
            print(f"  [OK] Loaded transactions file: {len(self.transactions_df)} records")
            
            # Basic validation
            if 'IG_ID' not in self.companies_df.columns:
                raise ValueError("IG_ID column missing in companies file")
            if 'IG_ID' not in self.transactions_df.columns:
                raise ValueError("IG_ID column missing in transactions file")
                
            return True
        except Exception as e:
            print(f"  [ERROR] Failed to load data: {e}")
            return False
    
    def check_structural_integrity(self):
        """Phase 2: Structural integrity checks"""
        print("\n[PHASE 2] Checking structural integrity...")
        
        # Check IG_ID format in transactions
        print("  Checking transaction IG_IDs...")
        invalid_tx_ids = []
        for idx, row in self.transactions_df.iterrows():
            ig_id = str(row['IG_ID'])
            if pd.isna(row['IG_ID']):
                invalid_tx_ids.append({'row': idx + 2, 'value': 'NULL'})
            elif not ig_id.replace('.0', '').isdigit():
                invalid_tx_ids.append({'row': idx + 2, 'value': ig_id})
        
        if invalid_tx_ids:
            self.issues['invalid_transaction_ids'] = invalid_tx_ids
            print(f"    [WARNING] Found {len(invalid_tx_ids)} invalid transaction IG_IDs")
        else:
            print(f"    [OK] All {len(self.transactions_df)} transaction IG_IDs are valid")
        
        # Check IG_ID format in companies
        print("  Checking company IG_IDs...")
        invalid_company_ids = []
        companies_with_ig_id = 0
        
        for idx, row in self.companies_df.iterrows():
            if pd.notna(row['IG_ID']) and str(row['IG_ID']).strip():
                companies_with_ig_id += 1
                ig_ids = str(row['IG_ID']).split(',')
                for ig_id in ig_ids:
                    ig_id = ig_id.strip()
                    if not ig_id.replace('.0', '').isdigit():
                        invalid_company_ids.append({
                            'company': row['name'],
                            'row': idx + 2,
                            'invalid_id': ig_id,
                            'full_value': row['IG_ID']
                        })
        
        if invalid_company_ids:
            self.issues['invalid_company_ids'] = invalid_company_ids
            print(f"    [WARNING] Found {len(invalid_company_ids)} invalid company IG_IDs")
        else:
            print(f"    [OK] All company IG_IDs are valid")
        
        print(f"    [INFO] {companies_with_ig_id}/{len(self.companies_df)} companies have IG_IDs")
        
        # Check role field consistency
        print("  Checking role field consistency...")
        role_issues = []
        for idx, row in self.companies_df.iterrows():
            if pd.notna(row['IG_ID']) and pd.notna(row['ig_role']):
                ig_ids = str(row['IG_ID']).split(',')
                roles = str(row['ig_role']).split(',')
                
                if len(ig_ids) != len(roles):
                    role_issues.append({
                        'company': row['name'],
                        'ig_id_count': len(ig_ids),
                        'role_count': len(roles),
                        'ig_ids': row['IG_ID'],
                        'roles': row['ig_role']
                    })
        
        if role_issues:
            self.issues['role_count_mismatch'] = role_issues
            print(f"    [WARNING] Found {len(role_issues)} role count mismatches")
        else:
            print(f"    [OK] All role counts match IG_ID counts")
        
        return True
    
    def validate_bidirectional_connections(self):
        """Phase 3: Bidirectional IG_ID validation"""
        print("\n[PHASE 3] Validating bidirectional IG_ID connections...")
        
        # Build lookup sets
        tx_ig_ids = set(self.transactions_df['IG_ID'].dropna().astype(str).str.replace('.0', ''))
        
        company_ig_ids = set()
        for ig_id_str in self.companies_df['IG_ID'].dropna():
            if str(ig_id_str).strip():
                for ig_id in str(ig_id_str).split(','):
                    company_ig_ids.add(ig_id.strip().replace('.0', ''))
        
        # Transaction -> Company direction
        print("  Checking Transaction -> Company linkage...")
        orphaned_transactions = tx_ig_ids - company_ig_ids
        
        if orphaned_transactions:
            self.issues['orphaned_transactions'] = list(orphaned_transactions)
            print(f"    [WARNING] Found {len(orphaned_transactions)} orphaned transaction IDs")
            print(f"    Examples: {list(orphaned_transactions)[:5]}")
        else:
            print(f"    [OK] All {len(tx_ig_ids)} transaction IDs are referenced in companies")
        
        # Company -> Transaction direction
        print("  Checking Company -> Transaction linkage...")
        phantom_ids = company_ig_ids - tx_ig_ids
        
        if phantom_ids:
            self.issues['phantom_company_ids'] = list(phantom_ids)
            print(f"    [WARNING] Found {len(phantom_ids)} phantom IG_IDs in companies")
            print(f"    Examples: {list(phantom_ids)[:5]}")
        else:
            print(f"    [OK] All {len(company_ig_ids)} company IG_IDs exist in transactions")
        
        # Calculate coverage statistics
        self.statistics['total_transactions'] = len(self.transactions_df)
        self.statistics['total_companies'] = len(self.companies_df)
        self.statistics['linked_transactions'] = len(tx_ig_ids - orphaned_transactions)
        self.statistics['orphaned_transactions'] = len(orphaned_transactions)
        self.statistics['phantom_ids'] = len(phantom_ids)
        
        return True
    
    def verify_role_consistency(self):
        """Phase 4: Role consistency verification"""
        print("\n[PHASE 4] Verifying role consistency...")
        
        # Build transaction role mapping
        tx_roles = defaultdict(lambda: {'targets': [], 'leads': [], 'participants': []})
        
        for idx, row in self.companies_df.iterrows():
            if pd.notna(row['IG_ID']) and pd.notna(row['ig_role']):
                ig_ids = str(row['IG_ID']).split(',')
                roles = str(row['ig_role']).split(',')
                company_name = row['name']
                
                for ig_id, role in zip(ig_ids, roles):
                    ig_id = ig_id.strip().replace('.0', '')
                    role = role.strip()
                    
                    if role == 'target':
                        tx_roles[ig_id]['targets'].append(company_name)
                    elif role == 'lead':
                        tx_roles[ig_id]['leads'].append(company_name)
                    elif role == 'participant':
                        tx_roles[ig_id]['participants'].append(company_name)
        
        # Check one target per transaction rule
        print("  Checking one target per transaction rule...")
        multiple_targets = []
        no_targets = []
        
        for ig_id in set(self.transactions_df['IG_ID'].dropna().astype(str).str.replace('.0', '')):
            if ig_id in tx_roles:
                targets = tx_roles[ig_id]['targets']
                if len(targets) > 1:
                    multiple_targets.append({
                        'ig_id': ig_id,
                        'targets': targets,
                        'count': len(targets)
                    })
                elif len(targets) == 0:
                    no_targets.append(ig_id)
            else:
                no_targets.append(ig_id)
        
        if multiple_targets:
            self.issues['multiple_targets'] = multiple_targets
            print(f"    [WARNING] {len(multiple_targets)} transactions have multiple targets")
        else:
            print(f"    [OK] No transactions have multiple targets")
        
        if no_targets:
            self.issues['no_targets'] = no_targets
            print(f"    [WARNING] {len(no_targets)} transactions have no targets")
        else:
            print(f"    [OK] All transactions have targets")
        
        # Check for same company as target and investor
        print("  Checking for target-investor conflicts...")
        target_investor_conflicts = []
        
        for ig_id, roles_dict in tx_roles.items():
            targets = set(roles_dict['targets'])
            investors = set(roles_dict['leads'] + roles_dict['participants'])
            
            conflicts = targets & investors
            if conflicts:
                target_investor_conflicts.append({
                    'ig_id': ig_id,
                    'conflicting_companies': list(conflicts)
                })
        
        if target_investor_conflicts:
            self.issues['target_investor_conflicts'] = target_investor_conflicts
            print(f"    [WARNING] {len(target_investor_conflicts)} transactions have target-investor conflicts")
        else:
            print(f"    [OK] No target-investor conflicts found")
        
        # Statistics
        self.statistics['transactions_with_targets'] = len([k for k, v in tx_roles.items() if v['targets']])
        self.statistics['avg_investors_per_transaction'] = np.mean([
            len(v['leads']) + len(v['participants']) 
            for v in tx_roles.values()
        ])
        
        return True
    
    def analyze_data_quality(self):
        """Phase 5: Data quality analysis"""
        print("\n[PHASE 5] Analyzing data quality...")
        
        # Check for duplicate company names with different IDs
        print("  Checking for duplicate company names...")
        name_groups = self.companies_df.groupby('name')['id'].nunique()
        duplicates = name_groups[name_groups > 1]
        
        if len(duplicates) > 0:
            duplicate_details = []
            for name in duplicates.index:
                companies = self.companies_df[self.companies_df['name'] == name]
                duplicate_details.append({
                    'name': name,
                    'ids': list(companies['id'].unique()),
                    'count': len(companies)
                })
            self.issues['duplicate_names'] = duplicate_details
            print(f"    [WARNING] Found {len(duplicates)} duplicate company names")
        else:
            print(f"    [OK] No duplicate company names found")
        
        # Check for companies without IDs but with IG_IDs
        print("  Checking for companies without Arcadia IDs...")
        no_id_with_ig = self.companies_df[
            (self.companies_df['id'].isna()) & 
            (self.companies_df['IG_ID'].notna())
        ]
        
        if len(no_id_with_ig) > 0:
            self.statistics['companies_without_arcadia_id'] = len(no_id_with_ig)
            print(f"    [INFO] {len(no_id_with_ig)} companies have IG_IDs but no Arcadia IDs")
            
            # Group by status
            status_counts = no_id_with_ig['status'].value_counts()
            for status, count in status_counts.items():
                print(f"      - {status}: {count}")
        
        # Check for parsing artifacts
        print("  Checking for parsing artifacts...")
        parsing_issues = []
        
        for idx, row in self.companies_df.iterrows():
            name = str(row['name'])
            # Check for common parsing issues
            if any(x in name for x in [' / ', ' // ', ' & ', '  ', '()', '[]']):
                parsing_issues.append({
                    'company': name,
                    'potential_issue': 'delimiter or empty brackets'
                })
        
        if parsing_issues:
            self.issues['parsing_artifacts'] = parsing_issues[:10]  # Limit to first 10
            print(f"    [WARNING] Found {len(parsing_issues)} potential parsing artifacts")
        else:
            print(f"    [OK] No obvious parsing artifacts found")
        
        return True
    
    def generate_statistical_analysis(self):
        """Phase 6: Statistical analysis"""
        print("\n[PHASE 6] Generating statistical analysis...")
        
        # Transaction coverage
        companies_with_ig = self.companies_df[self.companies_df['IG_ID'].notna()]
        
        # Role distribution
        role_counts = Counter()
        for roles in companies_with_ig['ig_role'].dropna():
            for role in str(roles).split(','):
                role_counts[role.strip()] += 1
        
        self.statistics['role_distribution'] = dict(role_counts)
        
        # Companies per transaction
        ig_id_counts = Counter()
        for ig_ids in companies_with_ig['IG_ID'].dropna():
            for ig_id in str(ig_ids).split(','):
                ig_id_counts[ig_id.strip()] += 1
        
        self.statistics['avg_companies_per_transaction'] = np.mean(list(ig_id_counts.values()))
        self.statistics['max_companies_per_transaction'] = max(ig_id_counts.values()) if ig_id_counts else 0
        self.statistics['min_companies_per_transaction'] = min(ig_id_counts.values()) if ig_id_counts else 0
        
        # Status distribution
        status_counts = self.companies_df['status'].value_counts()
        self.statistics['status_distribution'] = status_counts.to_dict()
        
        # Coverage percentages
        total_tx = len(self.transactions_df)
        linked_tx = self.statistics.get('linked_transactions', 0)
        self.statistics['transaction_coverage_pct'] = (linked_tx / total_tx * 100) if total_tx > 0 else 0
        
        print(f"  Transaction coverage: {self.statistics['transaction_coverage_pct']:.1f}%")
        print(f"  Average companies per transaction: {self.statistics['avg_companies_per_transaction']:.2f}")
        print(f"  Role distribution: {role_counts.most_common(3)}")
        
        return True
    
    def generate_reports(self):
        """Phase 7: Generate comprehensive reports"""
        print("\n[PHASE 7] Generating verification reports...")
        
        # Console summary
        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        
        total_issues = sum(len(v) for v in self.issues.values())
        
        if total_issues == 0:
            print("[SUCCESS] No critical issues found!")
            print("\nData Integrity Status: VERIFIED")
        else:
            print(f"[WARNING] Found {total_issues} total issues across {len(self.issues)} categories")
            print("\nIssue Summary:")
            for issue_type, issue_list in self.issues.items():
                print(f"  - {issue_type}: {len(issue_list)} issues")
        
        print("\nKey Statistics:")
        print(f"  Total transactions: {self.statistics['total_transactions']}")
        print(f"  Total companies: {self.statistics['total_companies']}")
        print(f"  Transaction coverage: {self.statistics['transaction_coverage_pct']:.1f}%")
        print(f"  Companies without Arcadia ID: {self.statistics.get('companies_without_arcadia_id', 0)}")
        
        # Save detailed reports
        if self.issues:
            # Create detailed issue report
            report_lines = []
            report_lines.append("# IG_ID Verification Issues Report")
            report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")
            
            for issue_type, issue_list in self.issues.items():
                report_lines.append(f"## {issue_type.replace('_', ' ').title()}")
                report_lines.append(f"Count: {len(issue_list)}")
                report_lines.append("")
                
                if len(issue_list) > 0 and isinstance(issue_list[0], dict):
                    # Format as table
                    if len(issue_list) <= 20:
                        for item in issue_list:
                            report_lines.append(f"- {json.dumps(item, indent=2)}")
                    else:
                        for item in issue_list[:20]:
                            report_lines.append(f"- {json.dumps(item, indent=2)}")
                        report_lines.append(f"... and {len(issue_list) - 20} more")
                else:
                    # Simple list
                    if len(issue_list) <= 20:
                        for item in issue_list:
                            report_lines.append(f"- {item}")
                    else:
                        for item in issue_list[:20]:
                            report_lines.append(f"- {item}")
                        report_lines.append(f"... and {len(issue_list) - 20} more")
                report_lines.append("")
            
            with open('verification_ig_id_issues.md', 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            print(f"\n[OK] Detailed issues saved to: verification_ig_id_issues.md")
        
        # Save statistics
        stats_df = pd.DataFrame([self.statistics])
        stats_df.T.to_csv('verification_statistics.csv', header=['Value'])
        print(f"[OK] Statistics saved to: verification_statistics.csv")
        
        return True
    
    def run_verification(self):
        """Main verification process"""
        success = True
        
        if not self.load_data():
            return False
        
        success = success and self.check_structural_integrity()
        success = success and self.validate_bidirectional_connections()
        success = success and self.verify_role_consistency()
        success = success and self.analyze_data_quality()
        success = success and self.generate_statistical_analysis()
        success = success and self.generate_reports()
        
        print("\n" + "=" * 80)
        print("VERIFICATION COMPLETE")
        print("=" * 80)
        
        return success

if __name__ == "__main__":
    verifier = ComprehensiveIGIDVerification()
    verifier.run_verification()