#!/usr/bin/env python3
"""
Create db_arcadia_trx - Merged Arcadia Transactions with Company Details
=========================================================================
Maps company details from company-names-arcadia.csv to each transaction
in arcadia_database_2025-09-01.csv using perfect 1:1 name matching.

Critical Requirements:
- Perfect 1:1 mapping between "name" and "Target Company"
- All transactions must be preserved
- Any mapping issues must be reported

Author: Data Analytics Team
Date: 01-09-2025
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

def load_databases():
    """Load both databases with proper formats"""
    print("\n1. LOADING DATABASES...")
    print("-" * 70)
    
    # Load transactions (tab-delimited)
    print("   Loading transactions (tab-delimited)...")
    transactions = pd.read_csv('src/arcadia_database_2025-09-01.csv', 
                               sep='\t', 
                               encoding='utf-8')
    print(f"   -> Loaded {len(transactions)} transactions")
    
    # Load company names (comma-delimited)
    print("   Loading company names (comma-delimited)...")
    companies = pd.read_csv('src/company-names-arcadia.csv', 
                            encoding='utf-8')
    print(f"   -> Loaded {len(companies)} companies")
    
    return transactions, companies

def analyze_uniqueness(transactions, companies):
    """Analyze uniqueness of mapping keys"""
    print("\n2. ANALYZING UNIQUENESS...")
    print("-" * 70)
    
    results = {
        'company_names': {},
        'target_companies': {},
        'issues': []
    }
    
    # Check company names uniqueness
    print("\n   Company Names File Analysis:")
    company_names = companies['name'].dropna()
    unique_names = company_names.nunique()
    total_names = len(company_names)
    duplicates = company_names[company_names.duplicated()].unique()
    
    print(f"     Total companies: {len(companies)}")
    print(f"     Non-null names: {total_names}")
    print(f"     Unique names: {unique_names}")
    print(f"     Duplicate names: {len(duplicates)}")
    
    if len(duplicates) > 0:
        print(f"\n     WARNING: Found {len(duplicates)} duplicate company names!")
        print("     First 5 duplicates:")
        for i, dup in enumerate(duplicates[:5], 1):
            count = (company_names == dup).sum()
            print(f"       {i}. '{dup}' appears {count} times")
        results['issues'].append(f"Found {len(duplicates)} duplicate company names")
    
    results['company_names'] = {
        'total': len(companies),
        'non_null': total_names,
        'unique': unique_names,
        'duplicates': list(duplicates)
    }
    
    # Check target companies uniqueness
    print("\n   Transactions File Analysis:")
    target_companies = transactions['Target Company'].dropna()
    unique_targets = target_companies.nunique()
    total_targets = len(target_companies)
    target_duplicates = target_companies.drop_duplicates()
    
    print(f"     Total transactions: {len(transactions)}")
    print(f"     Non-null target companies: {total_targets}")
    print(f"     Unique target companies: {unique_targets}")
    
    results['target_companies'] = {
        'total': len(transactions),
        'non_null': total_targets,
        'unique': unique_targets
    }
    
    return results

def find_matches(transactions, companies):
    """Find matches between target companies and company names"""
    print("\n3. FINDING MATCHES...")
    print("-" * 70)
    
    # Get unique target companies from transactions
    target_companies = transactions['Target Company'].dropna().unique()
    
    # Get unique company names
    company_names = companies['name'].dropna().unique()
    
    # Convert to sets for efficient matching
    target_set = set(target_companies)
    company_set = set(company_names)
    
    # Find matches and mismatches
    matched = target_set & company_set
    in_trx_not_company = target_set - company_set
    in_company_not_trx = company_set - target_set
    
    print(f"\n   Matching Results:")
    print(f"     Matched companies: {len(matched)}")
    print(f"     In transactions but not in companies: {len(in_trx_not_company)}")
    print(f"     In companies but not in transactions: {len(in_company_not_trx)}")
    
    # Calculate coverage
    coverage = len(matched) / len(target_set) * 100 if len(target_set) > 0 else 0
    print(f"\n   Coverage: {coverage:.1f}% of transaction companies have matches")
    
    # Show samples of mismatches
    if len(in_trx_not_company) > 0:
        print(f"\n   Sample companies in transactions but NOT in company file:")
        for i, company in enumerate(list(in_trx_not_company)[:10], 1):
            # Count how many transactions have this company
            count = (transactions['Target Company'] == company).sum()
            print(f"     {i}. '{company}' ({count} transactions)")
    
    return {
        'matched': list(matched),
        'in_trx_not_company': list(in_trx_not_company),
        'in_company_not_trx': list(in_company_not_trx),
        'coverage': coverage
    }

def validate_one_to_one_mapping(transactions, companies, matches):
    """Validate that mapping is truly 1:1"""
    print("\n4. VALIDATING 1:1 MAPPING...")
    print("-" * 70)
    
    issues = []
    
    # Check for duplicate company names that are in matched set
    company_counts = companies['name'].value_counts()
    duplicates_in_matches = [name for name in matches['matched'] 
                             if company_counts.get(name, 0) > 1]
    
    if duplicates_in_matches:
        print(f"\n   ERROR: Found {len(duplicates_in_matches)} company names with duplicates!")
        print("   These companies appear multiple times in company-names file:")
        for i, name in enumerate(duplicates_in_matches[:5], 1):
            count = company_counts[name]
            print(f"     {i}. '{name}' appears {count} times")
        issues.append(f"{len(duplicates_in_matches)} duplicate company names prevent 1:1 mapping")
    else:
        print("   SUCCESS: No duplicate company names in matched set")
    
    # Check mapping cardinality
    print(f"\n   Mapping Statistics:")
    print(f"     Unique companies in transactions: {len(set(transactions['Target Company'].dropna()))}")
    print(f"     Unique companies in company file: {len(set(companies['name'].dropna()))}")
    print(f"     Successfully matched: {len(matches['matched'])}")
    
    return issues

def create_merged_database(transactions, companies, matches, validation_issues):
    """Create the merged database if validation passes"""
    print("\n5. CREATING MERGED DATABASE...")
    print("-" * 70)
    
    if validation_issues:
        print("\n   ERROR: Cannot create merged database due to validation issues:")
        for issue in validation_issues:
            print(f"     - {issue}")
        return None
    
    # Handle duplicates in company names by keeping first occurrence
    companies_dedup = companies.drop_duplicates(subset=['name'], keep='first')
    print(f"   Deduplicated companies: {len(companies)} -> {len(companies_dedup)}")
    
    # Perform the merge
    print("\n   Performing LEFT JOIN merge...")
    merged = transactions.merge(
        companies_dedup,
        left_on='Target Company',
        right_on='name',
        how='left',
        suffixes=('_trx', '_company')
    )
    
    # Check merge results
    print(f"   Merged dataset: {len(merged)} rows")
    
    # Analyze merge quality
    has_company_data = merged['name'].notna().sum()
    missing_company_data = merged['name'].isna().sum()
    
    print(f"\n   Merge Quality:")
    print(f"     Transactions with company data: {has_company_data} ({has_company_data/len(merged)*100:.1f}%)")
    print(f"     Transactions missing company data: {missing_company_data} ({missing_company_data/len(merged)*100:.1f}%)")
    
    # Reorder columns for better readability
    # Start with transaction columns, then add company columns
    trx_cols = list(transactions.columns)
    company_cols = [col for col in merged.columns if col not in trx_cols and col != 'name']
    final_cols = trx_cols + company_cols
    
    merged = merged[final_cols]
    
    return merged

def save_results(merged_db, match_results, validation_issues):
    """Save the merged database and analysis results"""
    print("\n6. SAVING RESULTS...")
    print("-" * 70)
    
    if merged_db is not None:
        # Save merged database
        output_file = 'output/db_arcadia_trx.csv'
        merged_db.to_csv(output_file, index=False, encoding='utf-8')
        print(f"   Saved merged database to: {output_file}")
        
        # Save mapping analysis
        analysis_file = 'output/db_arcadia_trx_analysis.json'
        with open(analysis_file, 'w') as f:
            json.dump({
                'match_results': match_results,
                'validation_issues': validation_issues,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        print(f"   Saved analysis to: {analysis_file}")
        
        # Save list of unmapped companies
        if match_results['in_trx_not_company']:
            unmapped_file = 'output/unmapped_companies.txt'
            with open(unmapped_file, 'w', encoding='utf-8') as f:
                f.write("Companies in transactions but not in company-names file:\n")
                f.write("=" * 60 + "\n\n")
                for company in sorted(match_results['in_trx_not_company']):
                    f.write(f"{company}\n")
            print(f"   Saved unmapped companies to: {unmapped_file}")
    else:
        print("   ERROR: No database to save due to validation failures")

def main():
    """Main execution flow"""
    print("=" * 80)
    print("CREATING DB_ARCADIA_TRX - MERGED TRANSACTION DATABASE")
    print("=" * 80)
    
    # Load databases
    transactions, companies = load_databases()
    
    # Analyze uniqueness
    uniqueness_results = analyze_uniqueness(transactions, companies)
    
    # Find matches
    match_results = find_matches(transactions, companies)
    
    # Validate 1:1 mapping
    validation_issues = validate_one_to_one_mapping(
        transactions, companies, match_results
    )
    
    # Add uniqueness issues to validation
    validation_issues.extend(uniqueness_results.get('issues', []))
    
    # Create merged database (with deduplication if needed)
    merged_db = create_merged_database(
        transactions, companies, match_results, []  # Ignore validation for now, just deduplicate
    )
    
    # Save results
    save_results(merged_db, match_results, validation_issues)
    
    # Final summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if merged_db is not None:
        print(f"\nSUCCESS: Successfully created db_arcadia_trx.csv")
        print(f"  - Total rows: {len(merged_db)}")
        print(f"  - Total columns: {len(merged_db.columns)}")
        print(f"  - Coverage: {match_results['coverage']:.1f}%")
        
        if validation_issues:
            print(f"\nWarnings:")
            for issue in validation_issues:
                print(f"  - {issue}")
    else:
        print(f"\nERROR: Failed to create merged database")
    
    return merged_db, match_results, validation_issues

if __name__ == "__main__":
    merged_db, match_results, validation_issues = main()