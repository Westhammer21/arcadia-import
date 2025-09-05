"""
Arcadia Import Data Cleanup Script
Fixes critical data quality issues in arcadia_company_unmapped.csv
"""

import csv
import re
from typing import Dict, List, Tuple

def fix_status_values(status: str) -> str:
    """Fix invalid status values"""
    valid_statuses = {
        'ENABLED', 'DISABLED', 'TO_DELETE', 'IMPORTED', 'IS_INCOMPLETE', 'IS INCOMPLETE'
    }
    
    # Handle specific invalid values
    if status == 'TO BE CREATED':
        return 'IMPORTED'  # New external records should be marked as IMPORTED
    
    # Normalize IS INCOMPLETE variations
    if status == 'IS INCOMPLETE':
        return 'IS_INCOMPLETE'
    
    # Return as-is if valid
    if status in valid_statuses:
        return status
    
    # Default for any other invalid status
    return 'IS_INCOMPLETE'

def fix_type_values(type_val: str, company_name: str = '') -> str:
    """Fix invalid type values"""
    valid_types = {
        'Strategic / CVC',
        'Venture Capital & Accelerators', 
        'Private Equity & Inst.',
        'Other'
    }
    
    # Return if already valid
    if type_val in valid_types:
        return type_val
    
    # Map common invalid values
    type_mapping = {
        'TestType': 'Other',
        'Investor': 'Venture Capital & Accelerators',
        '': 'Other'
    }
    
    if type_val in type_mapping:
        return type_mapping[type_val]
    
    # Check if it's a malformed entry (contains company-like text)
    if any(keyword in type_val.lower() for keyword in ['ltd', 'inc', 'corp', 'games', 'ventures']):
        # Try to determine type from company name or default to Other
        if 'venture' in company_name.lower() or 'capital' in company_name.lower():
            return 'Venture Capital & Accelerators'
        elif 'equity' in company_name.lower():
            return 'Private Equity & Inst.'
        else:
            return 'Strategic / CVC'
    
    # Default for unrecognized types
    return 'Other'

def fix_country_values(country: str) -> Tuple[str, str]:
    """
    Fix invalid country values
    Returns: (country, status_override) - status_override if data is incomplete
    """
    # Handle known invalid values
    if country == 'notenoughinformation' or country == '':
        return '', 'IS_INCOMPLETE'
    
    # Check if it's a type value in country field (data corruption)
    if country in ['Strategic / CVC', 'Venture Capital & Accelerators', 'TestType', 'Investor']:
        return '', 'IS_INCOMPLETE'
    
    # Map common variations to ISO-style names
    country_mapping = {
        'United States': 'USA',
        'US': 'USA',
        'UK': 'United Kingdom',
        'Britain': 'United Kingdom',
        'South Korea': 'Korea',
        'UAE': 'United Arab Emirates',
        'Czech Republic': 'Czechia'
    }
    
    if country in country_mapping:
        return country_mapping[country], ''
    
    # Return as-is if it looks valid (contains only letters, spaces, and common punctuation)
    if re.match(r'^[A-Za-z\s\-\.]+$', country):
        return country, ''
    
    # Mark as incomplete for any other case
    return '', 'IS_INCOMPLETE'

def fix_founded_year(founded: str, status: str) -> Tuple[str, str]:
    """
    Fix invalid founded years
    Returns: (founded, status_override)
    """
    # Handle placeholder year
    if founded == '1800.0' or founded == '1800':
        return '', 'IS_INCOMPLETE'
    
    # Handle empty
    if not founded or founded == '':
        return '', 'IS_INCOMPLETE' if status != 'IS_INCOMPLETE' else status
    
    # Try to extract year from string
    try:
        year = int(float(founded))
        if 1800 <= year <= 2025:
            return str(year), status
        else:
            return '', 'IS_INCOMPLETE'
    except (ValueError, TypeError):
        return '', 'IS_INCOMPLETE'

def generate_arcadia_id(row_num: int, existing_ids: set) -> str:
    """Generate a new Arcadia ID for records without one"""
    # Start from a high number to avoid conflicts
    new_id = 20000 + row_num
    while str(new_id) in existing_ids:
        new_id += 1
    return str(new_id)

def clean_arcadia_data(input_file: str, output_file: str):
    """Main cleanup function"""
    
    # Read all data
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Collect existing IDs
    existing_ids = {row['id'] for row in rows if row['id']}
    
    # Statistics
    stats = {
        'total': len(rows),
        'status_fixed': 0,
        'type_fixed': 0,
        'country_fixed': 0,
        'founded_fixed': 0,
        'id_generated': 0,
        'marked_incomplete': 0
    }
    
    # Process each row
    cleaned_rows = []
    for i, row in enumerate(rows):
        cleaned = row.copy()
        
        # Fix status
        original_status = row['status']
        cleaned['status'] = fix_status_values(original_status)
        if original_status != cleaned['status']:
            stats['status_fixed'] += 1
        
        # Fix type
        original_type = row['type']
        cleaned['type'] = fix_type_values(original_type, row.get('name', ''))
        if original_type != cleaned['type']:
            stats['type_fixed'] += 1
        
        # Fix country
        original_country = row['hq_country']
        fixed_country, status_override = fix_country_values(original_country)
        cleaned['hq_country'] = fixed_country
        if status_override:
            cleaned['status'] = status_override
            stats['marked_incomplete'] += 1
        if original_country != cleaned['hq_country']:
            stats['country_fixed'] += 1
        
        # Fix founded year
        original_founded = row['founded']
        fixed_founded, status_override = fix_founded_year(original_founded, cleaned['status'])
        cleaned['founded'] = fixed_founded
        if status_override and cleaned['status'] != status_override:
            cleaned['status'] = status_override
            stats['marked_incomplete'] += 1
        if original_founded != cleaned['founded']:
            stats['founded_fixed'] += 1
        
        # Generate ID if missing
        if not row['id']:
            cleaned['id'] = generate_arcadia_id(i, existing_ids)
            existing_ids.add(cleaned['id'])
            stats['id_generated'] += 1
        
        # Clear AUM for non-investor types
        if cleaned['type'] not in ['Venture Capital & Accelerators', 'Private Equity & Inst.']:
            cleaned['aum'] = ''
        
        cleaned_rows.append(cleaned)
    
    # Write cleaned data
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        if cleaned_rows:
            writer = csv.DictWriter(f, fieldnames=cleaned_rows[0].keys())
            writer.writeheader()
            writer.writerows(cleaned_rows)
    
    # Print statistics
    print("=" * 60)
    print("ARCADIA DATA CLEANUP COMPLETED")
    print("=" * 60)
    print(f"Total records processed: {stats['total']}")
    print(f"Status values fixed: {stats['status_fixed']}")
    print(f"Type values fixed: {stats['type_fixed']}")
    print(f"Country values fixed: {stats['country_fixed']}")
    print(f"Founded years fixed: {stats['founded_fixed']}")
    print(f"IDs generated: {stats['id_generated']}")
    print(f"Records marked incomplete: {stats['marked_incomplete']}")
    print("=" * 60)
    print(f"Output file: {output_file}")
    
    return stats

def validate_cleaned_data(file_path: str) -> Dict:
    """Validate the cleaned data against Arcadia requirements"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    valid_statuses = {'ENABLED', 'DISABLED', 'TO_DELETE', 'IMPORTED', 'IS_INCOMPLETE'}
    valid_types = {'Strategic / CVC', 'Venture Capital & Accelerators', 'Private Equity & Inst.', 'Other'}
    
    issues = {
        'invalid_status': [],
        'invalid_type': [],
        'missing_required': [],
        'business_rule_violations': []
    }
    
    for i, row in enumerate(rows):
        # Check status
        if row['status'] not in valid_statuses:
            issues['invalid_status'].append(f"Row {i+2}: {row['status']}")
        
        # Check type
        if row['type'] not in valid_types:
            issues['invalid_type'].append(f"Row {i+2}: {row['type']}")
        
        # Check required fields
        required = ['name', 'type', 'status']
        for field in required:
            if not row.get(field):
                issues['missing_required'].append(f"Row {i+2}: Missing {field}")
        
        # Check business rules
        if row['type'] not in ['Venture Capital & Accelerators', 'Private Equity & Inst.'] and row.get('aum'):
            issues['business_rule_violations'].append(f"Row {i+2}: Non-investor has AUM value")
    
    return issues

if __name__ == "__main__":
    import os
    
    # File paths
    base_dir = r"C:\Users\sergei\Documents\VS-Code\transactions-check"
    input_file = os.path.join(base_dir, "output", "arcadia_company_unmapped.csv")
    output_file = os.path.join(base_dir, "output", "arcadia_company_unmapped_CLEANED.csv")
    
    # Run cleanup
    print("Starting Arcadia data cleanup...")
    stats = clean_arcadia_data(input_file, output_file)
    
    # Validate cleaned data
    print("\nValidating cleaned data...")
    issues = validate_cleaned_data(output_file)
    
    print("\nValidation Results:")
    print("-" * 40)
    
    all_clear = True
    for issue_type, issue_list in issues.items():
        if issue_list:
            all_clear = False
            print(f"\n{issue_type}: {len(issue_list)} issues")
            for issue in issue_list[:5]:  # Show first 5 issues
                print(f"  - {issue}")
            if len(issue_list) > 5:
                print(f"  ... and {len(issue_list) - 5} more")
    
    if all_clear:
        print("✓ All validations passed! File is ready for import.")
    else:
        print("\n✗ Issues remain. Manual review required.")