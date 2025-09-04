#!/usr/bin/env python3
"""
Precise Duplicate Analysis Between Arcadia and InvestGame
==========================================================
Analyzes potential duplicates using 4 specific matching criteria:
1. Date match: Announcement Date = Date
2. Size match: Transaction Size within ±5% or ±$0.2M
3. URL similarity: Source URL matches Deal Link at 95%+
4. Company similarity: Target Company matches Target name at 95%+

Author: Data Analytics Team
Date: 01-09-2025
"""

import pandas as pd
import numpy as np
from datetime import datetime
from difflib import SequenceMatcher
import re
from typing import Dict, List, Tuple
import json

def normalize_url(url: str) -> str:
    """Normalize URL for comparison by removing protocol and www"""
    if pd.isna(url) or not url:
        return ""
    
    url = str(url).lower().strip()
    # Remove protocol
    url = re.sub(r'^https?://', '', url)
    # Remove www
    url = re.sub(r'^www\.', '', url)
    # Remove trailing slash
    url = url.rstrip('/')
    return url

def normalize_company_name(name: str) -> str:
    """Normalize company name for comparison"""
    if pd.isna(name) or not name:
        return ""
    
    name = str(name).lower().strip()
    # Remove common suffixes
    name = re.sub(r'\b(inc|llc|ltd|limited|corp|corporation|gmbh|ag|sa|plc)\b', '', name)
    # Remove special characters
    name = re.sub(r'[^\w\s]', ' ', name)
    # Remove extra spaces
    name = ' '.join(name.split())
    return name

def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity between two strings using SequenceMatcher"""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1, str2).ratio() * 100

def check_date_match(date1, date2) -> bool:
    """Check if two dates match"""
    if pd.isna(date1) or pd.isna(date2):
        return False
    
    # Convert to datetime if string
    if isinstance(date1, str):
        try:
            date1 = pd.to_datetime(date1, dayfirst=True)
        except:
            return False
    if isinstance(date2, str):
        try:
            date2 = pd.to_datetime(date2, dayfirst=True)
        except:
            return False
    
    # Compare dates (ignore time)
    return date1.date() == date2.date()

def check_size_match(size1: float, size2: float) -> Tuple[bool, float]:
    """
    Check if sizes match within ±5% or ±$0.2M
    Returns (match_status, percentage_difference)
    """
    # Handle null/zero values
    if pd.isna(size1) or pd.isna(size2):
        return False, 0.0
    
    size1 = float(size1)
    size2 = float(size2)
    
    # If both are zero, they match
    if size1 == 0 and size2 == 0:
        return True, 0.0
    
    # If only one is zero, they don't match
    if size1 == 0 or size2 == 0:
        return False, 100.0
    
    # Calculate absolute and percentage difference
    abs_diff = abs(size1 - size2)
    pct_diff = (abs_diff / max(size1, size2)) * 100
    
    # Match if within ±5% OR within ±$0.2M
    matches = (pct_diff <= 5.0) or (abs_diff <= 0.2)
    
    return matches, pct_diff

def analyze_match(arc_row, ig_row) -> Dict:
    """
    Analyze match between an Arcadia and InvestGame transaction
    Returns detailed match information
    """
    result = {
        'arc_id': arc_row['ID'],
        'ig_id': ig_row['IG_ID'],
        'conditions_met': 0,
        'date_match': False,
        'size_match': False,
        'url_match': False,
        'company_match': False,
        'size_diff_pct': 0.0,
        'url_similarity': 0.0,
        'company_similarity': 0.0,
        'details': []
    }
    
    # 1. Check date match
    date_match = check_date_match(arc_row['Announcement date*'], ig_row['Date'])
    result['date_match'] = date_match
    if date_match:
        result['conditions_met'] += 1
        result['details'].append(f"Date match: {arc_row['Announcement date*']}")
    
    # 2. Check size match
    arc_size = arc_row.get('Transaction Size*, $M', 0)
    ig_size = ig_row.get('Size, $m', 0)
    size_match, size_diff = check_size_match(arc_size, ig_size)
    result['size_match'] = size_match
    result['size_diff_pct'] = size_diff
    if size_match:
        result['conditions_met'] += 1
        result['details'].append(f"Size match: ${arc_size}M vs ${ig_size}M ({size_diff:.1f}% diff)")
    
    # 3. Check URL similarity
    arc_url = normalize_url(arc_row.get('Source URL*', ''))
    ig_url = normalize_url(ig_row.get('Deal Link', ''))
    if arc_url and ig_url:
        url_sim = calculate_similarity(arc_url, ig_url)
        result['url_similarity'] = url_sim
        if url_sim >= 95.0:
            result['url_match'] = True
            result['conditions_met'] += 1
            result['details'].append(f"URL match: {url_sim:.1f}% similarity")
    
    # 4. Check company name similarity
    arc_company = normalize_company_name(arc_row.get('Target Company', ''))
    ig_company = normalize_company_name(ig_row.get('Target name', ''))
    if arc_company and ig_company:
        company_sim = calculate_similarity(arc_company, ig_company)
        result['company_similarity'] = company_sim
        if company_sim >= 95.0:
            result['company_match'] = True
            result['conditions_met'] += 1
            result['details'].append(f"Company match: {company_sim:.1f}% similarity")
    
    return result

def main():
    print("=" * 80)
    print("PRECISE DUPLICATE ANALYSIS - 4 CRITERIA MATCHING")
    print("=" * 80)
    
    # Load databases
    print("\n1. LOADING DATABASES...")
    arc = pd.read_csv('output/arcadia_new.csv', encoding='utf-8')
    ig = pd.read_csv('output/investgame_new.csv', encoding='utf-8')
    
    print(f"   Arcadia: {len(arc)} transactions")
    print(f"   InvestGame: {len(ig)} transactions")
    
    # Parse dates
    print("\n2. PARSING DATES...")
    arc['Announcement date*'] = pd.to_datetime(arc['Announcement date*'], errors='coerce')
    ig['Date'] = pd.to_datetime(ig['Date'], format='%d/%m/%Y', errors='coerce')
    
    # Analyze all potential matches
    print("\n3. ANALYZING ALL POTENTIAL MATCHES...")
    print("   This will take a few minutes...")
    
    all_matches = []
    perfect_matches = []  # All 4 conditions met
    strong_matches = []   # 3 out of 4 conditions
    
    # Track statistics
    stats = {
        'by_conditions': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0},
        'by_criteria': {
            'date': 0,
            'size': 0,
            'url': 0,
            'company': 0
        }
    }
    
    # Compare each Arcadia transaction with all InvestGame transactions
    for arc_idx, arc_row in arc.iterrows():
        best_match = None
        best_score = 0
        
        for ig_idx, ig_row in ig.iterrows():
            match_result = analyze_match(arc_row, ig_row)
            
            # Track statistics
            if match_result['conditions_met'] > 0:
                all_matches.append(match_result)
                
                # Update best match for this Arcadia transaction
                if match_result['conditions_met'] > best_score:
                    best_match = match_result
                    best_score = match_result['conditions_met']
                
                # Categorize matches
                if match_result['conditions_met'] == 4:
                    perfect_matches.append(match_result)
                elif match_result['conditions_met'] == 3:
                    strong_matches.append(match_result)
        
        # Update statistics
        if best_match:
            stats['by_conditions'][best_score] += 1
    
    # Calculate criteria statistics
    for match in all_matches:
        if match['date_match']:
            stats['by_criteria']['date'] += 1
        if match['size_match']:
            stats['by_criteria']['size'] += 1
        if match['url_match']:
            stats['by_criteria']['url'] += 1
        if match['company_match']:
            stats['by_criteria']['company'] += 1
    
    # Display results
    print("\n4. RESULTS SUMMARY")
    print("-" * 70)
    print(f"Perfect matches (4/4 criteria): {len(perfect_matches)}")
    print(f"Strong matches (3/4 criteria): {len(strong_matches)}")
    print(f"Total matches with 1+ criteria: {len(all_matches)}")
    
    print("\n5. DISTRIBUTION BY CONDITIONS MET")
    print("-" * 70)
    for conditions, count in sorted(stats['by_conditions'].items(), reverse=True):
        if count > 0:
            pct = (count / len(arc)) * 100
            print(f"  {conditions}/4 conditions: {count} transactions ({pct:.1f}%)")
    
    print("\n6. CRITERIA MATCH FREQUENCY")
    print("-" * 70)
    for criteria, count in stats['by_criteria'].items():
        print(f"  {criteria.capitalize()} matches: {count}")
    
    # Show perfect matches
    if perfect_matches:
        print("\n7. PERFECT MATCHES (ALL 4 CRITERIA MET)")
        print("-" * 70)
        for i, match in enumerate(perfect_matches[:10], 1):
            print(f"\n  Match #{i}:")
            print(f"    Arcadia ID: {match['arc_id']}")
            print(f"    InvestGame ID: {match['ig_id']}")
            for detail in match['details']:
                print(f"    - {detail}")
        
        if len(perfect_matches) > 10:
            print(f"\n  ... and {len(perfect_matches) - 10} more perfect matches")
    
    # Show strong matches
    if strong_matches:
        print("\n8. STRONG MATCHES (3/4 CRITERIA MET)")
        print("-" * 70)
        for i, match in enumerate(strong_matches[:5], 1):
            print(f"\n  Match #{i}:")
            print(f"    Arcadia ID: {match['arc_id']}")
            print(f"    InvestGame ID: {match['ig_id']}")
            print(f"    Missing criteria: ", end="")
            missing = []
            if not match['date_match']:
                missing.append('Date')
            if not match['size_match']:
                missing.append('Size')
            if not match['url_match']:
                missing.append('URL')
            if not match['company_match']:
                missing.append('Company')
            print(', '.join(missing))
        
        if len(strong_matches) > 5:
            print(f"\n  ... and {len(strong_matches) - 5} more strong matches")
    
    # Save detailed results
    print("\n9. SAVING DETAILED RESULTS...")
    
    # Save perfect matches
    if perfect_matches:
        perfect_df = pd.DataFrame(perfect_matches)
        perfect_df.to_csv('output/perfect_matches_4_criteria.csv', index=False)
        print(f"   Saved {len(perfect_matches)} perfect matches to perfect_matches_4_criteria.csv")
    
    # Save strong matches
    if strong_matches:
        strong_df = pd.DataFrame(strong_matches)
        strong_df.to_csv('output/strong_matches_3_criteria.csv', index=False)
        print(f"   Saved {len(strong_matches)} strong matches to strong_matches_3_criteria.csv")
    
    # Save summary statistics
    with open('output/duplicate_analysis_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
        print("   Saved statistics to duplicate_analysis_stats.json")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    
    # Final verdict
    if len(perfect_matches) > 0:
        print(f"\nFOUND {len(perfect_matches)} DEFINITE DUPLICATES (4/4 criteria)")
        print(f"FOUND {len(strong_matches)} PROBABLE DUPLICATES (3/4 criteria)")
        print("\nRECOMMENDATION: Review and exclude these duplicates before further analysis")
    else:
        print("\nNO PERFECT DUPLICATES FOUND")
        print("The databases appear to have been properly cleaned of duplicates")

if __name__ == "__main__":
    main()