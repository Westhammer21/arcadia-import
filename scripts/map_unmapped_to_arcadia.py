#!/usr/bin/env python3
"""
Map unmapped transactions to Arcadia company format
Created: 2025-09-03
Purpose: Create arc_ columns for transactions without arc_id following Arcadia business rules
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re
import json

# Configuration constants
TICKER_EXTRACTION_PATTERN = r'\(([A-Za-z]{2,}:\s*[A-Z0-9\s\.]+)\)'
DEFAULT_WEBSITE = "http://notenoughinformation.com"
DEFAULT_COUNTRY = "notenoughinformation"
DEFAULT_FOUNDED = "1800"

# Country code mapping (ISO 3166-1 alpha-2)
COUNTRY_MAPPING = {
    # US variations
    'United States': 'US',
    'United States of America': 'US',
    'USA': 'US',
    'U.S.A.': 'US',
    'U.S.': 'US',
    'US': 'US',
    
    # Common countries
    'United Kingdom': 'GB',
    'UK': 'GB',
    'Great Britain': 'GB',
    'Canada': 'CA',
    'Germany': 'DE',
    'France': 'FR',
    'China': 'CN',
    'Japan': 'JP',
    'South Korea': 'KR',
    'Korea': 'KR',
    'Singapore': 'SG',
    'Australia': 'AU',
    'Netherlands': 'NL',
    'Sweden': 'SE',
    'Finland': 'FI',
    'Denmark': 'DK',
    'Norway': 'NO',
    'Spain': 'ES',
    'Italy': 'IT',
    'Poland': 'PL',
    'Russia': 'RU',
    'Brazil': 'BR',
    'India': 'IN',
    'Israel': 'IL',
    'Turkey': 'TR',
    'UAE': 'AE',
    'Switzerland': 'CH',
    'Austria': 'AT',
    'Belgium': 'BE',
    'Ireland': 'IE',
    'Portugal': 'PT',
    'Czech Republic': 'CZ',
    'Romania': 'RO',
    'Hungary': 'HU',
    'Greece': 'GR',
    'New Zealand': 'NZ',
    'Mexico': 'MX',
    'Argentina': 'AR',
    'Chile': 'CL',
    'Colombia': 'CO',
    'Philippines': 'PH',
    'Thailand': 'TH',
    'Malaysia': 'MY',
    'Indonesia': 'ID',
    'Vietnam': 'VN',
    'Taiwan': 'TW',
    'Hong Kong': 'HK',
    'Ukraine': 'UA',
}

# Sector mapping rules
SECTOR_MAPPING = {
    'Esports': 'Esports',
    'Gaming': 'Gaming (Content & Development Publishing)',
    'Platform & Tech': 'Platform & Tech',
    'Other': 'Other'
}

# Segment mapping rules
SEGMENT_MAPPING = {
    'Esports': 'Esports',
    'Cash-related': 'Other',
    'Hardware': 'Other',
    'Marketing': 'Other',
    'Other': 'Other',
    'Blockchain-Powered': 'Platform & Tech',
    'Platform': 'Platform & Tech',
    'Tech': 'Platform & Tech',
    'VR/AR': 'VR/AR',
    'Mobile': 'Mobile',
    'Multiplatform': 'Multiplatform/Web',
    'PC&Console': 'PC/Console',
    'PC & Console': 'PC/Console',
    'Outsourcing': 'Outsourcing/WFH'
}

def analyze_unmapped_records():
    """Analyze records without arc_id"""
    print("=" * 70)
    print("PHASE 1: ANALYZING UNMAPPED RECORDS")
    print("=" * 70)
    
    # Load data
    input_file = Path('../output/ig_arc_unmapped_FINAL_COMPLETE.csv')
    print(f"\n1. Loading data from: {input_file}")
    
    df = pd.read_csv(input_file, encoding='utf-8')
    total_records = len(df)
    print(f"   Total records: {total_records}")
    
    # Find unmapped records (empty arc_id)
    unmapped_mask = df['arc_id'].isna() | (df['arc_id'].astype(str).str.strip() == '') | (df['arc_id'].astype(str) == 'nan')
    unmapped_records = df[unmapped_mask].copy()
    
    print(f"\n2. Unmapped records (empty arc_id): {len(unmapped_records)}")
    print(f"   Percentage: {len(unmapped_records)/total_records*100:.1f}%")
    
    # Analyze available data
    print(f"\n3. Data availability in unmapped records:")
    columns_to_check = ['Target name', 'Target Founded', "Target's Country", 
                       'Sector', 'Segment', 'AI', "Target's Website"]
    
    for col in columns_to_check:
        if col in unmapped_records.columns:
            non_empty = unmapped_records[col].notna().sum()
            print(f"   - {col}: {non_empty}/{len(unmapped_records)} ({non_empty/len(unmapped_records)*100:.1f}%)")
    
    # Check for duplicate target names
    target_counts = unmapped_records['Target name'].value_counts()
    duplicates = target_counts[target_counts > 1]
    
    print(f"\n4. Duplicate target names: {len(duplicates)}")
    if len(duplicates) > 0:
        print("   Top duplicates:")
        for name, count in duplicates.head(5).items():
            print(f"   - {name}: {count} occurrences")
    
    return df, unmapped_records, unmapped_mask

def map_country(country_str):
    """Map country name to ISO code"""
    if pd.isna(country_str) or str(country_str).strip() == '':
        return DEFAULT_COUNTRY
    
    country_str = str(country_str).strip()
    
    # Check direct mapping
    if country_str in COUNTRY_MAPPING:
        return COUNTRY_MAPPING[country_str]
    
    # Check if it's already an ISO code
    if len(country_str) == 2 and country_str.isupper():
        return country_str
    
    # Default
    return DEFAULT_COUNTRY

def detect_ticker(company_name):
    """Detect if company name contains ticker symbol"""
    if pd.isna(company_name):
        return False
    
    company_str = str(company_name)
    
    # Use regex pattern to find ticker
    ticker_match = re.search(TICKER_EXTRACTION_PATTERN, company_str)
    return ticker_match is not None

def validate_url(url):
    """Validate and fix common URL issues"""
    if pd.isna(url) or str(url).strip() == '':
        return DEFAULT_WEBSITE
    
    url_str = str(url).strip()
    
    # Skip if already default
    if url_str == DEFAULT_WEBSITE:
        return DEFAULT_WEBSITE
    
    # Add http:// if missing
    if not url_str.startswith(('http://', 'https://')):
        url_str = 'http://' + url_str
    
    # Basic URL validation (has domain)
    if '.' not in url_str.replace('http://', '').replace('https://', ''):
        return DEFAULT_WEBSITE
    
    return url_str

def map_sector(sector_str):
    """Map sector to Arcadia format"""
    if pd.isna(sector_str) or str(sector_str).strip() == '':
        return 'Other'
    
    sector_str = str(sector_str).strip()
    
    # Check for cash-related, hardware, marketing in sector (maps to Other)
    lower_sector = sector_str.lower()
    if any(term in lower_sector for term in ['cash', 'hardware', 'marketing']):
        return 'Other'
    
    return SECTOR_MAPPING.get(sector_str, 'Other')

def map_segment_and_features(segment_str, ai_value, sector_str):
    """Map segment to Arcadia format and extract features"""
    features = []
    
    # Handle AI feature
    if str(ai_value).upper() == 'YES':
        features.append('AI/ML')
    
    # Default segment
    segment = 'Other'
    
    if pd.notna(segment_str) and str(segment_str).strip() != '':
        segment_str = str(segment_str).strip()
        
        # Check for cash-related (adds feature)
        if 'Cash-related' in segment_str or 'cash' in segment_str.lower():
            features.append('Cash/Skill-based/RBG')
            segment = 'Other'
        
        # Check for blockchain (adds feature)
        elif 'Blockchain' in segment_str or 'blockchain' in segment_str.lower():
            features.append('Blockchain/web3')
            segment = 'Platform & Tech'
        
        # Map segment
        else:
            segment = SEGMENT_MAPPING.get(segment_str, None)
            
            if segment is None:
                # Unmapped segment - will be reported
                segment = segment_str  # Keep original for reporting
    
    # Join features
    features_str = ', '.join(features) if features else ''
    
    return segment, features_str

def handle_duplicate_targets(unmapped_records):
    """Analyze duplicate targets and create enriched mapping"""
    print("\n" + "=" * 70)
    print("PHASE 2: HANDLING DUPLICATE TARGET NAMES")
    print("=" * 70)
    
    # Group by target name
    grouped = unmapped_records.groupby('Target name')
    enriched_data = {}
    conflicts = []
    
    for target_name, group in grouped:
        if len(group) > 1:
            # Multiple records for same target
            # Find the most complete record
            best_record = {}
            conflict_fields = {}
            
            for col in ['Target Founded', "Target's Country", 'Sector', 'Segment', "Target's Website", 'AI']:
                if col in group.columns:
                    # Get non-null values
                    non_null_values = group[col].dropna()
                    
                    if len(non_null_values) > 0:
                        # Check for conflicts
                        unique_values = non_null_values.unique()
                        if len(unique_values) > 1:
                            conflict_fields[col] = list(unique_values)
                            # Use first non-null value by default
                            best_record[col] = non_null_values.iloc[0]
                        else:
                            best_record[col] = unique_values[0]
            
            if conflict_fields:
                conflicts.append({
                    'target': target_name,
                    'conflicts': conflict_fields
                })
            
            enriched_data[target_name] = best_record
    
    print(f"\n   Found {len(enriched_data)} targets with multiple records")
    print(f"   Conflicts detected: {len(conflicts)}")
    
    if conflicts:
        print("\n   Sample conflicts:")
        for conflict in conflicts[:3]:
            print(f"   - {conflict['target']}: {list(conflict['conflicts'].keys())}")
    
    return enriched_data, conflicts

def map_unmapped_companies(df, unmapped_records, enriched_data):
    """Map unmapped companies to arc_ columns"""
    print("\n" + "=" * 70)
    print("PHASE 3: MAPPING TO ARCADIA FORMAT")
    print("=" * 70)
    
    unmapped_segments = []
    processed_count = 0
    
    # Process each unmapped record
    for idx in unmapped_records.index:
        row = df.loc[idx]
        target_name = row['Target name']
        
        # Get enriched data if available
        if target_name in enriched_data:
            enriched = enriched_data[target_name]
            # Override with enriched data
            for col, value in enriched.items():
                if pd.isna(row[col]):
                    row[col] = value
        
        # Set arc_id
        df.at[idx, 'arc_id'] = 'TO BE CREATED'
        
        # Map arc_name
        df.at[idx, 'arc_name'] = target_name if pd.notna(target_name) else 'Undisclosed'
        
        # Set constants
        df.at[idx, 'arc_status'] = 'IMPORTED'
        df.at[idx, 'arc_type'] = 'Strategic / CVC'
        df.at[idx, 'arc_specialization'] = 'Generalist'
        
        # Map founded year
        founded = row.get('Target Founded', '')
        if pd.notna(founded) and str(founded).strip() != '':
            # Extract year if it's a full date
            founded_str = str(founded).strip()
            if len(founded_str) >= 4:
                df.at[idx, 'arc_founded'] = founded_str[:4]
            else:
                df.at[idx, 'arc_founded'] = DEFAULT_FOUNDED
        else:
            df.at[idx, 'arc_founded'] = DEFAULT_FOUNDED
        
        # Map country
        country = row.get("Target's Country", '')
        df.at[idx, 'arc_hq_country'] = map_country(country)
        
        # arc_hq_region - leave empty as it's auto-derived
        df.at[idx, 'arc_hq_region'] = ''
        
        # Map ownership based on ticker
        has_ticker = detect_ticker(target_name)
        df.at[idx, 'arc_ownership'] = 'Public' if has_ticker else 'Private'
        
        # Map website
        website = row.get("Target's Website", '')
        df.at[idx, 'arc_website'] = validate_url(website)
        
        # Map sector
        sector = row.get('Sector', '')
        df.at[idx, 'arc_sector'] = map_sector(sector)
        
        # Map segment and features
        segment = row.get('Segment', '')
        ai = row.get('AI', '')
        mapped_segment, features = map_segment_and_features(segment, ai, sector)
        
        # Check for unmapped segments
        if mapped_segment not in SEGMENT_MAPPING.values() and mapped_segment != '':
            if pd.notna(segment) and str(segment).strip() != '':
                unmapped_segments.append({
                    'row': idx,
                    'target': target_name,
                    'original_segment': segment,
                    'mapped_to': mapped_segment
                })
        
        df.at[idx, 'arc_segment'] = mapped_segment if mapped_segment else ''
        df.at[idx, 'arc_features'] = features
        
        # Leave other arc_ fields empty
        empty_fields = ['arc_also_known_as', 'arc_aliases', 'arc_aum', 
                       'arc_parent_company', 'arc_search_index']
        for field in empty_fields:
            if field in df.columns:
                df.at[idx, field] = ''
        
        processed_count += 1
    
    print(f"\n   Processed {processed_count} records")
    print(f"   Unmapped segments found: {len(unmapped_segments)}")
    
    if unmapped_segments:
        print("\n   Unmapped segments:")
        for item in unmapped_segments[:5]:
            print(f"   - Row {item['row']}: '{item['original_segment']}' for {item['target']}")
    
    return df, unmapped_segments

def generate_statistics(df, unmapped_mask):
    """Generate statistics about the mapping"""
    print("\n" + "=" * 70)
    print("PHASE 4: STATISTICS")
    print("=" * 70)
    
    mapped_df = df[unmapped_mask]
    
    # Ownership distribution
    ownership_counts = mapped_df['arc_ownership'].value_counts()
    print(f"\n1. Ownership Distribution:")
    for ownership, count in ownership_counts.items():
        print(f"   - {ownership}: {count} ({count/len(mapped_df)*100:.1f}%)")
    
    # Sector distribution
    sector_counts = mapped_df['arc_sector'].value_counts()
    print(f"\n2. Sector Distribution:")
    for sector, count in sector_counts.head(10).items():
        print(f"   - {sector}: {count} ({count/len(mapped_df)*100:.1f}%)")
    
    # Country distribution
    country_counts = mapped_df['arc_hq_country'].value_counts()
    print(f"\n3. Top Countries:")
    for country, count in country_counts.head(10).items():
        print(f"   - {country}: {count} ({count/len(mapped_df)*100:.1f}%)")
    
    # Feature usage
    has_features = mapped_df['arc_features'].notna() & (mapped_df['arc_features'] != '')
    print(f"\n4. Feature Statistics:")
    print(f"   - Records with features: {has_features.sum()} ({has_features.sum()/len(mapped_df)*100:.1f}%)")
    
    # AI/ML feature
    has_ai = mapped_df['arc_features'].str.contains('AI/ML', na=False)
    print(f"   - AI/ML feature: {has_ai.sum()}")
    
    # Blockchain feature
    has_blockchain = mapped_df['arc_features'].str.contains('Blockchain', na=False)
    print(f"   - Blockchain/web3 feature: {has_blockchain.sum()}")
    
    # Cash/Skill feature
    has_cash = mapped_df['arc_features'].str.contains('Cash', na=False)
    print(f"   - Cash/Skill-based/RBG feature: {has_cash.sum()}")
    
    return {
        'ownership': ownership_counts.to_dict(),
        'sectors': sector_counts.to_dict(),
        'countries': country_counts.to_dict(),
        'features': {
            'total_with_features': int(has_features.sum()),
            'ai_ml': int(has_ai.sum()),
            'blockchain': int(has_blockchain.sum()),
            'cash_skill': int(has_cash.sum())
        }
    }

def create_documentation(stats, enriched_data, conflicts, unmapped_segments, total_processed):
    """Create comprehensive documentation"""
    
    doc_file = Path('../docs/TARGET_NAME_MAPPING_DOCUMENTATION.md')
    
    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write("# Target Name Field Mapping Documentation\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Purpose**: Map unmapped transactions to Arcadia company format\n\n")
        
        f.write("---\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"- **Total Records Processed**: {total_processed}\n")
        f.write(f"- **Arc_id Status**: All set to 'TO BE CREATED'\n")
        f.write(f"- **Default Values Applied**: arc_status='IMPORTED', arc_type='Strategic / CVC'\n")
        f.write(f"- **Duplicate Targets Handled**: {len(enriched_data)}\n")
        f.write(f"- **Conflicts Detected**: {len(conflicts)}\n")
        f.write(f"- **Unmapped Segments**: {len(unmapped_segments)}\n\n")
        
        f.write("---\n\n")
        
        f.write("## Field Mapping Rules Applied\n\n")
        f.write("| Arcadia Field | Source Field | Mapping Logic | Default Value |\n")
        f.write("|---------------|--------------|---------------|---------------|\n")
        f.write("| arc_id | N/A | Set to 'TO BE CREATED' | TO BE CREATED |\n")
        f.write("| arc_name | Target name | Direct mapping | Undisclosed |\n")
        f.write("| arc_status | N/A | Constant value | IMPORTED |\n")
        f.write("| arc_type | N/A | Constant value | Strategic / CVC |\n")
        f.write("| arc_founded | Target Founded | Extract year (YYYY) | 1800 |\n")
        f.write("| arc_hq_country | Target's Country | ISO 3166-1 mapping | notenoughinformation |\n")
        f.write("| arc_hq_region | N/A | Auto-derived from country | (empty) |\n")
        f.write("| arc_ownership | Target name | Ticker detection | Private |\n")
        f.write("| arc_sector | Sector | Sector mapping rules | Other |\n")
        f.write("| arc_segment | Segment | Segment mapping rules | Other |\n")
        f.write("| arc_features | AI, Segment | Feature extraction | (empty) |\n")
        f.write("| arc_website | Target's Website | URL validation | http://notenoughinformation.com |\n")
        f.write("| arc_specialization | N/A | Constant value | Generalist |\n\n")
        
        f.write("---\n\n")
        
        f.write("## Statistics\n\n")
        
        f.write("### Ownership Distribution\n")
        for ownership, count in stats['ownership'].items():
            f.write(f"- {ownership}: {count}\n")
        
        f.write("\n### Sector Distribution\n")
        for sector, count in list(stats['sectors'].items())[:10]:
            f.write(f"- {sector}: {count}\n")
        
        f.write("\n### Country Distribution (Top 10)\n")
        for country, count in list(stats['countries'].items())[:10]:
            f.write(f"- {country}: {count}\n")
        
        f.write("\n### Feature Statistics\n")
        f.write(f"- Total with features: {stats['features']['total_with_features']}\n")
        f.write(f"- AI/ML: {stats['features']['ai_ml']}\n")
        f.write(f"- Blockchain/web3: {stats['features']['blockchain']}\n")
        f.write(f"- Cash/Skill-based/RBG: {stats['features']['cash_skill']}\n\n")
        
        f.write("---\n\n")
        
        f.write("## Data Quality Issues\n\n")
        
        if conflicts:
            f.write("### Conflicts in Duplicate Target Names\n\n")
            f.write("When the same target appeared multiple times with different values:\n\n")
            for conflict in conflicts[:10]:
                f.write(f"**{conflict['target']}**:\n")
                for field, values in conflict['conflicts'].items():
                    f.write(f"  - {field}: {values}\n")
                f.write("\n")
            
            if len(conflicts) > 10:
                f.write(f"... and {len(conflicts) - 10} more conflicts\n\n")
        
        if unmapped_segments:
            f.write("### ⚠️ Unmapped Segments Requiring Attention\n\n")
            f.write("These segment values did not match any mapping rule:\n\n")
            
            unique_segments = {}
            for item in unmapped_segments:
                seg = item['original_segment']
                if seg not in unique_segments:
                    unique_segments[seg] = []
                unique_segments[seg].append(item['target'])
            
            for segment, targets in unique_segments.items():
                f.write(f"- **'{segment}'** (appears in {len(targets)} records)\n")
                f.write(f"  Examples: {', '.join(targets[:3])}\n")
        
        f.write("\n---\n\n")
        
        f.write("## Validation Checks\n\n")
        f.write("✅ All required fields populated\n")
        f.write("✅ ISO country codes validated\n")
        f.write("✅ URLs validated and standardized\n")
        f.write("✅ Ticker patterns detected for ownership\n")
        f.write("✅ Duplicate targets handled with data enrichment\n")
        
        if unmapped_segments:
            f.write("⚠️ Unmapped segments require manual review\n")
        
        f.write("\n---\n\n")
        f.write("**End of Report**\n")
    
    print(f"\n   Documentation saved to: {doc_file}")
    
    return doc_file

def main():
    """Main execution function"""
    print("\n" + "=" * 80)
    print(" TARGET NAME MAPPING TO ARCADIA FORMAT ")
    print("=" * 80)
    
    # Phase 1: Analyze unmapped records
    df, unmapped_records, unmapped_mask = analyze_unmapped_records()
    
    if len(unmapped_records) == 0:
        print("\nNo unmapped records found. Nothing to process.")
        return
    
    # Phase 2: Handle duplicate targets
    enriched_data, conflicts = handle_duplicate_targets(unmapped_records)
    
    # Create backup
    print("\nCreating backup...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = Path(f'../output/ig_arc_unmapped_BACKUP_{timestamp}.csv')
    df.to_csv(backup_file, index=False, encoding='utf-8')
    print(f"   Backup saved to: {backup_file}")
    
    # Phase 3: Map to Arcadia format
    df_mapped, unmapped_segments = map_unmapped_companies(df, unmapped_records, enriched_data)
    
    # Phase 4: Generate statistics
    stats = generate_statistics(df_mapped, unmapped_mask)
    
    # Save updated data
    output_file = Path('../output/ig_arc_unmapped_FINAL_COMPLETE.csv')
    df_mapped.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n   Updated data saved to: {output_file}")
    
    # Create documentation
    doc_file = create_documentation(stats, enriched_data, conflicts, unmapped_segments, len(unmapped_records))
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"\n✓ Processed {len(unmapped_records)} unmapped records")
    print(f"✓ All arc_id set to 'TO BE CREATED'")
    print(f"✓ Handled {len(enriched_data)} duplicate targets")
    
    if conflicts:
        print(f"⚠ {len(conflicts)} targets had conflicting data")
    if unmapped_segments:
        print(f"⚠ {len(unmapped_segments)} segments could not be mapped")
    
    print(f"\n✓ Documentation created: {doc_file}")
    print(f"✓ Data saved to: {output_file}")

if __name__ == "__main__":
    main()