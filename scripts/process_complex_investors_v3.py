#!/usr/bin/env python3
"""
Process Complex Investor Cases - Version 3
===========================================
Updated logic for 4+ investors without delimiters:
- 2-3 investors: all marked as lead
- 4+ investors: lead = "Undisclosed", all actual investors as participants

Author: AI Analytics Team
Date: 2025-01-09
"""

import pandas as pd
import re
from pathlib import Path
from datetime import datetime
import numpy as np

def parse_investor_string(investor_str):
    """
    Parse investor string to identify leads and participants
    
    Updated Rules:
    1. If "(lead)" exists - use LAST occurrence to split
    2. If "/" exists (no lead) - use FIRST occurrence to split  
    3. No delimiter + 2-3 investors = all are leads
    4. No delimiter + 4+ investors = lead is "Undisclosed", all are participants
    """
    if pd.isna(investor_str) or investor_str == '':
        return [], [], 'empty'
    
    investor_str = str(investor_str).strip()
    
    # Find all occurrences of "(lead)" case-insensitive
    lead_pattern = r'\(lead\)'
    lead_matches = list(re.finditer(lead_pattern, investor_str, re.IGNORECASE))
    
    lead_investors = []
    participants = []
    parsing_method = ""
    
    if lead_matches:
        # Use LAST occurrence of "(lead)"
        last_lead_match = lead_matches[-1]
        split_pos = last_lead_match.start()
        
        # Everything before "(lead)" = lead investors
        lead_section = investor_str[:split_pos].strip()
        # Everything after "(lead)" = participants
        participant_section = investor_str[last_lead_match.end():].strip()
        
        parsing_method = "lead_marker"
        
        # Remove any trailing "/" or "," from lead section
        lead_section = lead_section.rstrip('/').rstrip(',').strip()
        # Remove any leading "/" or "," from participant section
        participant_section = participant_section.lstrip('/').lstrip(',').strip()
        
        # Split by comma and clean up
        if lead_section:
            lead_names = [name.strip() for name in lead_section.split(',') if name.strip()]
            lead_investors = [name for name in lead_names if len(name) >= 2]
        
        if participant_section:
            participant_names = [name.strip() for name in participant_section.split(',') if name.strip()]
            participants = [name for name in participant_names if len(name) >= 2]
            
    elif '/' in investor_str:
        # Use FIRST "/" to split
        parts = investor_str.split('/', 1)  # Split only at first occurrence
        lead_section = parts[0].strip()
        participant_section = parts[1].strip() if len(parts) > 1 else ""
        parsing_method = "slash_delimiter"
        
        # Split by comma and clean up
        if lead_section:
            lead_names = [name.strip() for name in lead_section.split(',') if name.strip()]
            lead_investors = [name for name in lead_names if len(name) >= 2]
        
        if participant_section:
            participant_names = [name.strip() for name in participant_section.split(',') if name.strip()]
            participants = [name for name in participant_names if len(name) >= 2]
            
    else:
        # No clear delimiter - NEW LOGIC based on investor count
        all_names = [name.strip() for name in investor_str.split(',') if name.strip()]
        all_investors = [name for name in all_names if len(name) >= 2]
        
        if len(all_investors) <= 3:
            # 2-3 investors: all are leads
            lead_investors = all_investors
            participants = []
            parsing_method = f"no_delimiter_{len(all_investors)}_leads"
        else:
            # 4+ investors: lead is "Undisclosed", all are participants
            lead_investors = ["Undisclosed"]  # Special case
            participants = all_investors
            parsing_method = f"no_delimiter_{len(all_investors)}_undisclosed"
    
    return lead_investors, participants, parsing_method

def expand_transaction_rows(df_row, lead_investors, participants):
    """
    Create multiple rows from a single transaction - one per investor
    """
    expanded_rows = []
    
    # Create rows for lead investors
    for investor in lead_investors:
        new_row = df_row.copy()
        new_row['investor_name'] = investor
        new_row['investor_role'] = 'lead'
        new_row['investor_count'] = len(lead_investors) + len(participants)
        new_row['lead_count'] = len(lead_investors)
        new_row['participant_count'] = len(participants)
        # Also fill the ig_tier_lead_investor_acquirer for leads
        new_row['ig_tier_lead_investor_acquirer'] = investor
        expanded_rows.append(new_row)
    
    # Create rows for participants
    for investor in participants:
        new_row = df_row.copy()
        new_row['investor_name'] = investor
        new_row['investor_role'] = 'participant'
        new_row['investor_count'] = len(lead_investors) + len(participants)
        new_row['lead_count'] = len(lead_investors)
        new_row['participant_count'] = len(participants)
        # For participants, reference the first lead (might be "Undisclosed")
        if lead_investors:
            new_row['ig_tier_lead_investor_acquirer'] = lead_investors[0]
        expanded_rows.append(new_row)
    
    return expanded_rows

def process_complex_cases(df):
    """
    Process all complex investor cases with updated logic
    """
    print("\n" + "="*80)
    print("PROCESSING COMPLEX INVESTOR CASES - V3")
    print("="*80)
    
    # Identify complex cases (where ig_tier_lead_investor_acquirer is empty)
    complex_mask = (df['ig_tier_lead_investor_acquirer'].isna()) | (df['ig_tier_lead_investor_acquirer'] == '')
    complex_df = df[complex_mask].copy()
    simple_df = df[~complex_mask].copy()
    
    print(f"[INFO] Found {len(complex_df)} complex cases to process")
    print(f"[INFO] Keeping {len(simple_df)} simple cases as-is")
    
    # Process each complex case
    all_expanded_rows = []
    parsing_stats = {}
    error_cases = []
    undisclosed_lead_cases = []
    
    for idx, row in complex_df.iterrows():
        investor_str = row['Investors / Buyers']
        
        try:
            # Parse the investor string
            lead_investors, participants, parsing_method = parse_investor_string(investor_str)
            parsing_stats[parsing_method] = parsing_stats.get(parsing_method, 0) + 1
            
            # Track cases where we set lead as "Undisclosed"
            if "undisclosed" in parsing_method:
                undisclosed_lead_cases.append({
                    'target': row['Target name'],
                    'original': investor_str,
                    'investor_count': len(participants)
                })
            
            # Add parsing method to row
            row['parsing_method'] = parsing_method
            
            # Expand to multiple rows
            if lead_investors or participants:
                expanded_rows = expand_transaction_rows(row, lead_investors, participants)
                all_expanded_rows.extend(expanded_rows)
            else:
                # No valid investors found - keep original row with error flag
                row['parsing_method'] = 'error_no_investors'
                row['investor_name'] = 'PARSE_ERROR'
                row['investor_role'] = 'unknown'
                all_expanded_rows.append(row)
                error_cases.append({
                    'target': row['Target name'],
                    'original': investor_str,
                    'error': 'No valid investors parsed'
                })
                
        except Exception as e:
            print(f"[ERROR] Failed to parse: {investor_str}")
            print(f"        Error: {str(e)}")
            row['parsing_method'] = 'error_exception'
            row['investor_name'] = 'PARSE_ERROR'
            row['investor_role'] = 'unknown'
            all_expanded_rows.append(row)
            error_cases.append({
                'target': row['Target name'],
                'original': investor_str,
                'error': str(e)
            })
    
    # Convert expanded rows to DataFrame
    expanded_df = pd.DataFrame(all_expanded_rows)
    
    # Add metadata columns to simple_df for consistency
    simple_df['investor_name'] = simple_df['Investors / Buyers']
    simple_df['investor_role'] = 'lead'  # Simple cases are all leads
    simple_df['investor_count'] = 1
    simple_df['lead_count'] = 1
    simple_df['participant_count'] = 0
    simple_df['parsing_method'] = 'simple_case'
    
    # Combine simple and expanded dataframes
    final_df = pd.concat([simple_df, expanded_df], ignore_index=True)
    
    # Sort by IG_ID for better organization
    final_df = final_df.sort_values(['IG_ID', 'investor_role', 'investor_name'])
    
    print(f"\n[STATS] Parsing Method Distribution:")
    for method, count in sorted(parsing_stats.items()):
        print(f"         {method}: {count}")
    
    print(f"\n[RESULT] Original rows: {len(df)}")
    print(f"[RESULT] Expanded rows: {len(final_df)}")
    print(f"[RESULT] Row increase: {len(final_df) - len(df)} rows")
    print(f"[RESULT] Error cases: {len(error_cases)}")
    print(f"[RESULT] Cases with Undisclosed lead: {len(undisclosed_lead_cases)}")
    
    return final_df, error_cases, undisclosed_lead_cases

def validate_sample(df, sample_size=50):
    """
    Validate a sample of processed transactions
    """
    print("\n" + "="*80)
    print("VALIDATION OF SAMPLE TRANSACTIONS")
    print("="*80)
    
    # Get unique transaction IDs that were complex cases
    complex_ids = df[df['parsing_method'] != 'simple_case']['IG_ID'].unique()
    
    # Sample up to 50 transactions
    sample_ids = np.random.choice(complex_ids, 
                                 min(sample_size, len(complex_ids)), 
                                 replace=False)
    
    print(f"\n[VALIDATION] Sampling {len(sample_ids)} complex transactions")
    
    # Focus on undisclosed lead cases
    undisclosed_cases = df[df['parsing_method'].str.contains('undisclosed', na=False)]['IG_ID'].unique()
    
    if len(undisclosed_cases) > 0:
        print(f"\n[UNDISCLOSED LEAD CASES] Found {len(undisclosed_cases)} transactions")
        for ig_id in undisclosed_cases[:5]:  # Show first 5
            transaction_rows = df[df['IG_ID'] == ig_id]
            
            print(f"\n[Transaction ID: {ig_id}]")
            print(f"Target: {transaction_rows.iloc[0]['Target name']}")
            print(f"Original: {transaction_rows.iloc[0]['Investors / Buyers']}")
            print(f"Parsing Method: {transaction_rows.iloc[0]['parsing_method']}")
            print(f"Total Investors: {transaction_rows.iloc[0]['investor_count']}")
            print(f"Lead: {transaction_rows.iloc[0]['ig_tier_lead_investor_acquirer']}")
            print(f"Expanded to {len(transaction_rows)} rows:")
            
            for _, row in transaction_rows.iterrows():
                role_marker = "[L]" if row['investor_role'] == 'lead' else "[P]"
                print(f"  {role_marker} {row['investor_name']}")
    
    # Show regular validation
    validation_results = []
    
    print(f"\n[OTHER COMPLEX CASES SAMPLE]")
    for ig_id in sample_ids[:10]:  # Show first 10
        if ig_id in undisclosed_cases:
            continue  # Already shown above
            
        transaction_rows = df[df['IG_ID'] == ig_id]
        
        print(f"\n[Transaction ID: {ig_id}]")
        print(f"Target: {transaction_rows.iloc[0]['Target name']}")
        print(f"Parsing Method: {transaction_rows.iloc[0]['parsing_method']}")
        print(f"Total Investors: {transaction_rows.iloc[0]['investor_count']}")
        
        # Validation checks
        issues = []
        if any(transaction_rows['investor_name'].str.len() < 2):
            issues.append("Short investor name detected")
        if transaction_rows['investor_name'].isna().any():
            issues.append("Missing investor name")
        if transaction_rows['investor_name'].str.contains('PARSE_ERROR').any():
            issues.append("Parse error detected")
            
        validation_results.append({
            'ig_id': ig_id,
            'issues': issues,
            'status': 'PASS' if not issues else 'FAIL'
        })
    
    # Summary statistics
    print(f"\n[VALIDATION SUMMARY]")
    pass_count = sum(1 for r in validation_results if r['status'] == 'PASS')
    fail_count = len(validation_results) - pass_count
    print(f"Passed: {pass_count}/{len(validation_results)}")
    print(f"Failed: {fail_count}/{len(validation_results)}")
    
    return validation_results

def verify_final_table(df):
    """
    Verify the final table for correctness
    """
    print("\n" + "="*80)
    print("FINAL TABLE VERIFICATION")
    print("="*80)
    
    # Check for missing values in critical columns
    print(f"\n[COLUMN COMPLETENESS CHECK]")
    critical_cols = ['investor_name', 'investor_role', 'ig_tier_lead_investor_acquirer']
    for col in critical_cols:
        missing = df[col].isna().sum()
        empty = (df[col] == '').sum()
        print(f"  {col}: {missing} missing, {empty} empty")
    
    # Check role distribution
    print(f"\n[ROLE DISTRIBUTION]")
    role_counts = df['investor_role'].value_counts()
    for role, count in role_counts.items():
        print(f"  {role}: {count} ({count/len(df)*100:.1f}%)")
    
    # Check parsing method distribution
    print(f"\n[PARSING METHOD DISTRIBUTION]")
    method_counts = df['parsing_method'].value_counts()
    for method, count in method_counts.head(10).items():
        print(f"  {method}: {count}")
    
    # Verify undisclosed lead assignments
    undisclosed_leads = df[df['ig_tier_lead_investor_acquirer'] == 'Undisclosed']
    print(f"\n[UNDISCLOSED LEAD ASSIGNMENTS]")
    print(f"  Total rows with Undisclosed lead: {len(undisclosed_leads)}")
    print(f"  Unique transactions: {undisclosed_leads['IG_ID'].nunique()}")
    
    # Verify no data loss
    print(f"\n[DATA INTEGRITY]")
    print(f"  Unique IG_IDs: {df['IG_ID'].nunique()} (should be 883)")
    print(f"  Total rows: {len(df)}")
    
    return True

def main():
    """
    Main processing function
    """
    print("\n" + "="*80)
    print("COMPLEX INVESTOR PROCESSING PIPELINE - VERSION 3")
    print("="*80)
    print("[UPDATE] New logic for 4+ investors without delimiters:")
    print("  - 2-3 investors: all marked as lead")
    print("  - 4+ investors: lead='Undisclosed', all as participants")
    
    # Setup paths
    base_path = Path(__file__).parent.parent
    input_path = base_path / 'output' / 'ig_arc_unmapped_investors_v1.csv'
    output_path = base_path / 'output' / 'ig_arc_unmapped_investors_FINAL.csv'
    report_path = base_path / 'docs' / 'complex_investor_processing_report_FINAL.md'
    
    # Create backup
    backup_path = base_path / 'archive' / f'ig_arc_unmapped_investors_backup_v3_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    # Load data
    print(f"\n[LOADING] Reading from: {input_path}")
    df = pd.read_csv(input_path, encoding='utf-8')
    print(f"[OK] Loaded {len(df)} transactions")
    
    # Create backup
    backup_path.parent.mkdir(exist_ok=True)
    df.to_csv(backup_path, index=False, encoding='utf-8')
    print(f"[BACKUP] Saved to: {backup_path}")
    
    # Process complex cases with new logic
    processed_df, error_cases, undisclosed_lead_cases = process_complex_cases(df)
    
    # Validate sample
    validation_results = validate_sample(processed_df)
    
    # Verify final table
    verify_final_table(processed_df)
    
    # Save results
    processed_df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"\n[SAVED] Output file: {output_path}")
    print(f"[SAVED] Total rows: {len(processed_df)}")
    
    # Generate report
    report_content = f"""# Complex Investor Processing Report - FINAL
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Original Transactions**: {len(df)}
- **Simple Cases**: {(df['ig_tier_lead_investor_acquirer'] != '').sum()}
- **Complex Cases Processed**: {(df['ig_tier_lead_investor_acquirer'] == '').sum()}
- **Final Row Count**: {len(processed_df)}
- **Row Expansion**: {len(processed_df) - len(df)} additional rows

## New Logic Applied (V3)
- **2-3 investors without delimiter**: All marked as lead
- **4+ investors without delimiter**: Lead set as "Undisclosed", all actual investors as participants
- **Cases with Undisclosed lead**: {len(undisclosed_lead_cases)} transactions

## Processing Statistics
- **Lead marker "(lead)"**: {len(processed_df[processed_df['parsing_method'] == 'lead_marker'])} rows
- **Slash delimiter "/"**: {len(processed_df[processed_df['parsing_method'] == 'slash_delimiter'])} rows
- **No delimiter (2-3 investors)**: {len(processed_df[processed_df['parsing_method'].str.contains('no_delimiter_[23]_leads', na=False)])} rows
- **No delimiter (4+ investors)**: {len(processed_df[processed_df['parsing_method'].str.contains('undisclosed', na=False)])} rows
- **Simple cases**: {len(processed_df[processed_df['parsing_method'] == 'simple_case'])} rows

## Undisclosed Lead Cases
Total: {len(undisclosed_lead_cases)} transactions

### Examples:
"""
    
    for case in undisclosed_lead_cases[:10]:
        report_content += f"- **{case['target']}**: {case['investor_count']} investors → Lead='Undisclosed'\n"
    
    report_content += f"""

## Role Distribution
- **Lead roles**: {(processed_df['investor_role'] == 'lead').sum()}
- **Participant roles**: {(processed_df['investor_role'] == 'participant').sum()}

## Error Cases
Total errors: {len(error_cases)}
"""
    
    if error_cases:
        report_content += "\n### Error Details:\n"
        for error in error_cases[:10]:
            report_content += f"- **{error['target']}**: {error['error']}\n"
    
    report_content += f"""

## Validation Results
- Sample size: {len(validation_results)} transactions
- Passed: {sum(1 for r in validation_results if r['status'] == 'PASS')}
- Failed: {sum(1 for r in validation_results if r['status'] == 'FAIL')}

## Data Integrity Verification
- **Unique Transaction IDs**: {processed_df['IG_ID'].nunique()} (expected: 883)
- **Total Rows**: {len(processed_df)}
- **Rows with Undisclosed lead**: {(processed_df['ig_tier_lead_investor_acquirer'] == 'Undisclosed').sum()}

## Output File Structure
All original columns preserved plus:
- `investor_name`: Individual investor name
- `investor_role`: "lead" or "participant"
- `investor_count`: Total investors in transaction
- `lead_count`: Number of lead investors
- `participant_count`: Number of participants
- `parsing_method`: Method used to parse
- `ig_tier_lead_investor_acquirer`: Lead investor (might be "Undisclosed")
"""
    
    # Save report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"[REPORT] Saved to: {report_path}")
    
    return processed_df

if __name__ == "__main__":
    processed_df = main()