"""
Two-Pass Duplicate Analysis V2.0 - Improved Confidence Buckets
=============================================================
Author: Financial Analysis Team
Date: 2025-01-02
Version: 2.0

CONFIDENCE LEVELS:
- 100%: EXACT match (name/website/alias/known_as perfect match)
- 90%: Very high similarity (>90% name match + other criteria)
- 75%: High probability (>80% name match)
- 50%: Moderate probability (>70% name match)
- 40%: Date+Size match WITHOUT name match (special case)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
import warnings
warnings.filterwarnings('ignore')

def improved_two_pass_analysis():
    """Two-pass analysis with improved confidence buckets"""
    print("="*80)
    print("TWO-PASS DUPLICATE ANALYSIS V4.0 - ENHANCED CONFIDENCE BUCKETS")
    print("="*80)
    print(f"Start: {datetime.now().strftime('%H:%M:%S')}\n")
    
    # Load data from src folder
    print("Loading data...")
    investgame_df = pd.read_csv('src/investgame_database_mapped.csv', encoding='utf-8')
    arcadia_df = pd.read_csv('src/arcadia_database_with_ids.csv', encoding='utf-8')
    companies_df = pd.read_csv('src/company-names-arcadia.csv', encoding='utf-8')
    
    print(f"  InvestGame: {len(investgame_df)}")
    print(f"  Arcadia: {len(arcadia_df)}")
    
    # Convert dates
    investgame_df['Date'] = pd.to_datetime(investgame_df['Date'], format='%d/%m/%Y', errors='coerce')
    arcadia_df['Announcement date*'] = pd.to_datetime(arcadia_df['Announcement date*'], errors='coerce')
    
    # Filter date range
    start_date = pd.Timestamp('2020-01-01')
    end_date = pd.Timestamp('2025-05-31')
    
    investgame_df = investgame_df[
        (investgame_df['Date'] >= start_date) & 
        (investgame_df['Date'] <= end_date)
    ].reset_index(drop=False).rename(columns={'index': 'ig_id'})
    
    arcadia_df = arcadia_df[
        (arcadia_df['Announcement date*'] >= start_date) & 
        (arcadia_df['Announcement date*'] <= end_date) &
        (~arcadia_df['Status*'].isin(['TO DELETE', 'DISABLED']))
    ].reset_index(drop=False).rename(columns={'index': 'arc_id'})
    
    print(f"  After filter: IG {len(investgame_df)}, Arc {len(arcadia_df)}")
    
    # Build enhanced company lookup with all names and website info
    print("\nBuilding enhanced lookups...")
    company_lookup = {}
    website_lookup = {}
    
    for _, row in companies_df.iterrows():
        company_id = row['id']
        names = []
        
        # Collect all possible names
        if pd.notna(row.get('name')):
            names.append(str(row['name']).lower().strip())
        if pd.notna(row.get('also_known_as')):
            names.append(str(row['also_known_as']).lower().strip())
        if pd.notna(row.get('aliases')):
            for alias in str(row['aliases']).split(','):
                alias_clean = alias.lower().strip()
                if alias_clean:
                    names.append(alias_clean)
        if pd.notna(row.get('parent_company')):
            names.append(str(row['parent_company']).lower().strip())
            
        company_lookup[company_id] = list(set(names))  # Remove duplicates
        
        # Store website if available
        if pd.notna(row.get('website')):
            website_lookup[company_id] = str(row['website']).lower().strip()
    
    # Track matched transactions
    matched_ig = set()
    matched_arc = set()
    all_matches = []
    
    # ============================================
    # PASS 1: WITHIN CATEGORIES (±60 days)
    # ============================================
    print("\n" + "="*60)
    print("PASS 1: WITHIN CATEGORIES (with improved confidence)")
    print("="*60)
    
    pass1_start = datetime.now()
    pass1_comparisons = 0
    
    # Compatible categories
    category_map = {
        'Late-stage Investments': ['Late-stage Investments', 'Growth / Expansion'],
        'Growth / Expansion': ['Late-stage Investments', 'Growth / Expansion'],
        'Early-stage Investments': ['Early-stage Investments', 'Seed', 'Series A', 'Series B']
    }
    
    for category in investgame_df['Final_Category'].unique():
        if pd.isna(category):
            continue
        
        # Get compatible categories
        compatible = category_map.get(category, [category])
        
        ig_cat = investgame_df[
            (investgame_df['Final_Category'] == category) & 
            (~investgame_df['ig_id'].isin(matched_ig))
        ]
        arc_cat = arcadia_df[
            (arcadia_df['Transaction Category*'].isin(compatible)) &
            (~arcadia_df['arc_id'].isin(matched_arc))
        ]
        
        if len(ig_cat) == 0 or len(arc_cat) == 0:
            continue
        
        print(f"\n{category}: {len(ig_cat)} IG x {len(arc_cat)} Arc")
        
        cat_matches = []
        
        for _, ig_row in ig_cat.iterrows():
            ig_id = ig_row['ig_id']
            ig_date = ig_row['Date']
            ig_target = str(ig_row['Target name']).lower().strip()
            ig_size = float(ig_row.get('Size, $m', 0) or 0)
            ig_type = str(ig_row.get('Final_Type', '')).lower()
            
            if not ig_target:
                continue
            
            # Date range filter FIRST (optimization)
            date_min = ig_date - timedelta(days=60)
            date_max = ig_date + timedelta(days=60)
            
            arc_date_filtered = arc_cat[
                (arc_cat['Announcement date*'] >= date_min) &
                (arc_cat['Announcement date*'] <= date_max)
            ]
            
            if len(arc_date_filtered) == 0:
                continue
            
            best_match = None
            best_score = 0
            
            for _, arc_row in arc_date_filtered.iterrows():
                pass1_comparisons += 1
                arc_id = arc_row['arc_id']
                arc_date = arc_row['Announcement date*']
                arc_size = float(arc_row.get('Transaction Size*, $M', 0) or 0)
                arc_type = str(arc_row.get('Transaction Type*', '')).lower()
                
                # Get all possible names for this company
                company_id = arc_row.get('target_company_id')
                arc_names = [str(arc_row['Target Company']).lower().strip()]
                if pd.notna(company_id) and company_id in company_lookup:
                    arc_names.extend(company_lookup[company_id])
                
                # Calculate name matching score
                name_score = 0
                exact_match = False
                
                for arc_name in arc_names:
                    if ig_target == arc_name:
                        # EXACT match found!
                        name_score = 100
                        exact_match = True
                        break
                    else:
                        # Fuzzy matching
                        score = fuzz.ratio(ig_target, arc_name)
                        name_score = max(name_score, score)
                
                # Check website match if available (counts as exact match)
                if not exact_match and pd.notna(company_id) and company_id in website_lookup:
                    ig_website = str(ig_row.get('Website', '')).lower().strip()
                    if ig_website and ig_website == website_lookup[company_id]:
                        exact_match = True
                        name_score = 100
                
                # Skip if name score too low
                if name_score < 70:
                    continue
                
                # Calculate date difference
                date_diff = abs((arc_date - ig_date).days)
                
                # Check size match
                size_match = check_size_match(ig_size, arc_size)
                
                # Check type match
                type_match = check_type_match(ig_type, arc_type)
                
                # IMPROVED CONFIDENCE CALCULATION
                confidence = calculate_confidence_v2(
                    exact_match=exact_match,
                    name_score=name_score,
                    date_diff=date_diff,
                    size_match=size_match,
                    type_match=type_match,
                    category_match=True  # Within same/compatible categories
                )
                
                # Keep best match
                if confidence > 0 and name_score > best_score:
                    best_match = {
                        'confidence': confidence,
                        'ig_id': ig_id,
                        'arc_id': arc_id,
                        'ig_target': ig_row['Target name'],
                        'arc_target': arc_row['Target Company'],
                        'name_score': name_score,
                        'exact_match': exact_match,
                        'date_diff': date_diff,
                        'ig_date': ig_date.strftime('%Y-%m-%d'),
                        'arc_date': arc_date.strftime('%Y-%m-%d'),
                        'ig_size': ig_size,
                        'arc_size': arc_size,
                        'size_match': size_match,
                        'ig_type': ig_row.get('Final_Type', ''),
                        'arc_type': arc_row.get('Transaction Type*', ''),
                        'type_match': type_match,
                        'ig_category': category,
                        'arc_category': arc_row['Transaction Category*'],
                        'pass': 1
                    }
                    best_score = name_score
            
            if best_match:
                cat_matches.append(best_match)
                matched_ig.add(best_match['ig_id'])
                matched_arc.add(best_match['arc_id'])
        
        all_matches.extend(cat_matches)
        
        # Show distribution of matches
        if cat_matches:
            conf_dist = {}
            for m in cat_matches:
                conf = m['confidence']
                conf_dist[conf] = conf_dist.get(conf, 0) + 1
            print(f"  Found {len(cat_matches)} matches: ", end="")
            for conf in sorted(conf_dist.keys(), reverse=True):
                print(f"{conf}%:{conf_dist[conf]} ", end="")
            print()
    
    pass1_time = (datetime.now() - pass1_start).seconds
    print(f"\nPass 1 complete: {len(all_matches)} matches in {pass1_time}s")
    print(f"Comparisons: {pass1_comparisons:,}")
    
    # ============================================
    # PASS 2: BY DATE RANGES (cross-category)
    # ============================================
    print("\n" + "="*60)
    print("PASS 2: BY DATE RANGES (cross-category)")
    print("="*60)
    
    pass2_start = datetime.now()
    pass2_comparisons = 0
    
    # Get unmatched
    unmatched_ig = investgame_df[~investgame_df['ig_id'].isin(matched_ig)]
    unmatched_arc = arcadia_df[~arcadia_df['arc_id'].isin(matched_arc)]
    
    print(f"Unmatched: {len(unmatched_ig)} IG, {len(unmatched_arc)} Arc")
    
    # Sort by date for optimization
    unmatched_arc = unmatched_arc.sort_values('Announcement date*')
    
    # Process in weekly batches
    date_ranges = pd.date_range(start_date, end_date, freq='W')
    
    pass2_matches = []
    
    for i, week_start in enumerate(date_ranges):
        if i % 50 == 0:
            print(f"  Processing week {i}/{len(date_ranges)}...")
        
        week_end = week_start + timedelta(days=7)
        
        # Get transactions in this week
        ig_week = unmatched_ig[
            (unmatched_ig['Date'] >= week_start) &
            (unmatched_ig['Date'] < week_end)
        ]
        
        if len(ig_week) == 0:
            continue
        
        # Look for matches in ±90 day window
        arc_window = unmatched_arc[
            (unmatched_arc['Announcement date*'] >= week_start - timedelta(days=90)) &
            (unmatched_arc['Announcement date*'] <= week_end + timedelta(days=90))
        ]
        
        for _, ig_row in ig_week.iterrows():
            ig_id = ig_row['ig_id']
            ig_target = str(ig_row['Target name']).lower().strip()
            ig_date = ig_row['Date']
            ig_size = float(ig_row.get('Size, $m', 0) or 0)
            ig_type = str(ig_row.get('Final_Type', '')).lower()
            
            if not ig_target:
                continue
            
            best_match = None
            best_score = 0
            
            for _, arc_row in arc_window.iterrows():
                pass2_comparisons += 1
                arc_id = arc_row['arc_id']
                arc_date = arc_row['Announcement date*']
                arc_size = float(arc_row.get('Transaction Size*, $M', 0) or 0)
                arc_type = str(arc_row.get('Transaction Type*', '')).lower()
                
                # Get names
                company_id = arc_row.get('target_company_id')
                arc_names = [str(arc_row['Target Company']).lower().strip()]
                if pd.notna(company_id) and company_id in company_lookup:
                    arc_names.extend(company_lookup[company_id])
                
                # Name matching
                name_score = 0
                exact_match = False
                
                for arc_name in arc_names:
                    if ig_target == arc_name:
                        name_score = 100
                        exact_match = True
                        break
                    score = fuzz.ratio(ig_target, arc_name)
                    name_score = max(name_score, score)
                
                # For cross-category, require higher name threshold
                if name_score < 80:
                    continue
                
                date_diff = abs((arc_date - ig_date).days)
                size_match = check_size_match(ig_size, arc_size)
                type_match = check_type_match(ig_type, arc_type)
                
                # Calculate confidence for cross-category
                confidence = calculate_confidence_v2(
                    exact_match=exact_match,
                    name_score=name_score,
                    date_diff=date_diff,
                    size_match=size_match,
                    type_match=type_match,
                    category_match=False  # Cross-category
                )
                
                if confidence > 0 and name_score > best_score:
                    best_match = {
                        'confidence': confidence,
                        'ig_id': ig_id,
                        'arc_id': arc_id,
                        'ig_target': ig_row['Target name'],
                        'arc_target': arc_row['Target Company'],
                        'name_score': name_score,
                        'exact_match': exact_match,
                        'date_diff': date_diff,
                        'ig_date': ig_date.strftime('%Y-%m-%d'),
                        'arc_date': arc_date.strftime('%Y-%m-%d'),
                        'ig_size': ig_size,
                        'arc_size': arc_size,
                        'size_match': size_match,
                        'ig_type': ig_row.get('Final_Type', ''),
                        'arc_type': arc_row.get('Transaction Type*', ''),
                        'type_match': type_match,
                        'ig_category': ig_row['Final_Category'],
                        'arc_category': arc_row['Transaction Category*'],
                        'pass': 2
                    }
                    best_score = name_score
            
            if best_match:
                pass2_matches.append(best_match)
                matched_ig.add(best_match['ig_id'])
                matched_arc.add(best_match['arc_id'])
    
    all_matches.extend(pass2_matches)
    
    pass2_time = (datetime.now() - pass2_start).seconds
    print(f"\nPass 2 complete: {len(pass2_matches)} matches in {pass2_time}s")
    print(f"Comparisons: {pass2_comparisons:,}")
    
    # ============================================
    # PASS 3: 40% BUCKET - Date+Size WITHOUT Name
    # ============================================
    print("\n" + "="*60)
    print("PASS 3: 40% BUCKET - Date+Size+Type matches WITHOUT name")
    print("="*60)
    
    pass3_start = datetime.now()
    pass3_comparisons = 0
    
    # Get remaining unmatched
    unmatched_ig = investgame_df[~investgame_df['ig_id'].isin(matched_ig)]
    unmatched_arc = arcadia_df[~arcadia_df['arc_id'].isin(matched_arc)]
    
    print(f"Remaining unmatched: {len(unmatched_ig)} IG, {len(unmatched_arc)} Arc")
    
    pass3_matches = []
    
    # Look for date+size+type matches without name match
    for _, ig_row in unmatched_ig.iterrows():
        ig_id = ig_row['ig_id']
        ig_date = ig_row['Date']
        ig_size = float(ig_row.get('Size, $m', 0) or 0)
        ig_type = str(ig_row.get('Final_Type', '')).lower()
        ig_category = ig_row['Final_Category']
        
        # Skip if no size information
        if ig_size == 0:
            continue
        
        # Very tight date window for 40% matches
        date_min = ig_date - timedelta(days=14)
        date_max = ig_date + timedelta(days=14)
        
        # Find transactions with matching date and size
        arc_candidates = unmatched_arc[
            (unmatched_arc['Announcement date*'] >= date_min) &
            (unmatched_arc['Announcement date*'] <= date_max)
        ]
        
        for _, arc_row in arc_candidates.iterrows():
            pass3_comparisons += 1
            arc_id = arc_row['arc_id']
            arc_date = arc_row['Announcement date*']
            arc_size = float(arc_row.get('Transaction Size*, $M', 0) or 0)
            arc_type = str(arc_row.get('Transaction Type*', '')).lower()
            
            # Skip if no size
            if arc_size == 0:
                continue
            
            # Check if size matches closely
            size_diff = abs(ig_size - arc_size)
            size_pct = size_diff / max(ig_size, arc_size) * 100
            
            # Very strict size match for 40% bucket
            if size_pct > 5 and size_diff > 0.5:
                continue
            
            # Check type match
            if not check_type_match(ig_type, arc_type):
                continue
            
            # Check date proximity
            date_diff = abs((arc_date - ig_date).days)
            if date_diff > 14:
                continue
            
            # Calculate name score to ensure it's LOW (that's the point of 40% bucket)
            ig_target = str(ig_row['Target name']).lower().strip()
            arc_target = str(arc_row['Target Company']).lower().strip()
            name_score = fuzz.ratio(ig_target, arc_target)
            
            # Only include if name score is LOW (different companies but same transaction)
            if name_score >= 60:
                continue
            
            # This is a potential duplicate based on date+size+type but different name
            match = {
                'confidence': 40,
                'ig_id': ig_id,
                'arc_id': arc_id,
                'ig_target': ig_row['Target name'],
                'arc_target': arc_row['Target Company'],
                'name_score': name_score,
                'exact_match': False,
                'date_diff': date_diff,
                'ig_date': ig_date.strftime('%Y-%m-%d'),
                'arc_date': arc_date.strftime('%Y-%m-%d'),
                'ig_size': ig_size,
                'arc_size': arc_size,
                'size_match': True,
                'ig_type': ig_row.get('Final_Type', ''),
                'arc_type': arc_row.get('Transaction Type*', ''),
                'type_match': True,
                'ig_category': ig_category,
                'arc_category': arc_row['Transaction Category*'],
                'pass': 3,
                'note': 'Date+Size+Type match but DIFFERENT company names'
            }
            
            pass3_matches.append(match)
            matched_ig.add(ig_id)
            matched_arc.add(arc_id)
            break  # Only one match per transaction
    
    all_matches.extend(pass3_matches)
    
    pass3_time = (datetime.now() - pass3_start).seconds
    print(f"\nPass 3 complete: {len(pass3_matches)} potential misnamed duplicates in {pass3_time}s")
    print(f"Comparisons: {pass3_comparisons:,}")
    
    # ============================================
    # SAVE RESULTS
    # ============================================
    print("\n" + "="*60)
    print("FINAL RESULTS - V4.0")
    print("="*60)
    
    if all_matches:
        results_df = pd.DataFrame(all_matches)
        results_df = results_df.sort_values(['confidence', 'name_score'], ascending=[False, False])
        
        # Statistics
        print(f"Total duplicates found: {len(results_df)}")
        print(f"Pass 1 (within categories): {len(results_df[results_df['pass'] == 1])}")
        print(f"Pass 2 (cross-category): {len(results_df[results_df['pass'] == 2])}")
        print(f"Pass 3 (40% bucket): {len(results_df[results_df['pass'] == 3])}")
        
        # Confidence distribution
        print("\nConfidence distribution:")
        for conf in [100, 90, 75, 50, 40]:
            count = len(results_df[results_df['confidence'] == conf])
            if count > 0:
                pct = count / len(results_df) * 100
                print(f"  {conf}%: {count} ({pct:.1f}%)")
        
        # Exact matches
        exact_count = len(results_df[results_df['exact_match'] == True])
        print(f"\nExact name/alias matches: {exact_count}")
        
        # Save to output folder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"output/two_pass_v4_results_{timestamp}.csv"
        results_df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\nSaved to: {output_file}")
        
        # Summary
        print(f"\nTarget: ~3,900 duplicates")
        print(f"Found: {len(results_df)}")
        print(f"Achievement: {len(results_df)/3900*100:.1f}%")
        
        print(f"\nTotal comparisons: {pass1_comparisons + pass2_comparisons + pass3_comparisons:,}")
        print(f"Total time: {pass1_time + pass2_time + pass3_time}s")
        
        # Show sample of 40% bucket if any
        bucket_40 = results_df[results_df['confidence'] == 40]
        if len(bucket_40) > 0:
            print("\n" + "="*60)
            print("SAMPLE OF 40% BUCKET (Date+Size match, different names):")
            print("="*60)
            for _, row in bucket_40.head(5).iterrows():
                print(f"\nIG: {row['ig_target']} | Arc: {row['arc_target']}")
                print(f"  Date: {row['ig_date']} vs {row['arc_date']} ({row['date_diff']} days)")
                print(f"  Size: ${row['ig_size']}M vs ${row['arc_size']}M")
                print(f"  Type: {row['ig_type']} vs {row['arc_type']}")
                print(f"  Name similarity: {row['name_score']}%")
    else:
        print("No matches found!")
    
    print("\n" + "="*60)
    print(f"Complete: {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)

def calculate_confidence_v2(exact_match, name_score, date_diff, size_match, type_match, category_match):
    """
    Calculate confidence score with improved buckets:
    - 100%: EXACT match (name/website/alias exact match)
    - 90%: Very high similarity but not exact
    - 75%: High probability
    - 50%: Moderate probability
    - 40%: Special case (handled separately in Pass 3)
    """
    
    # 100% - EXACT MATCH
    if exact_match:
        # Perfect name match + other strong criteria
        if date_diff <= 35 and size_match and type_match and category_match:
            return 100
        # Perfect name but some criteria missing
        elif date_diff <= 60 and category_match:
            return 90
        # Perfect name but weaker criteria
        else:
            return 75
    
    # 90% - VERY HIGH SIMILARITY (not exact but >90% match)
    elif name_score >= 90:
        if date_diff <= 35 and size_match and type_match and category_match:
            return 90
        elif date_diff <= 60 and category_match:
            return 75
        else:
            return 50
    
    # 75% - HIGH PROBABILITY
    elif name_score >= 80:
        if date_diff <= 60 and category_match:
            return 75
        else:
            return 50
    
    # 50% - MODERATE PROBABILITY
    elif name_score >= 70:
        if date_diff <= 90:
            return 50
        else:
            return 0  # Too weak
    
    return 0

def check_size_match(size1, size2):
    """Check if transaction sizes match"""
    # Both undisclosed
    if size1 == 0 and size2 == 0:
        return True
    
    # One disclosed, one not
    if size1 == 0 or size2 == 0:
        return False
    
    # Both disclosed - check if within 10% or $1M
    pct_diff = abs(size1 - size2) / max(size1, size2) * 100
    abs_diff = abs(size1 - size2)
    
    return pct_diff <= 10 or abs_diff <= 1

def check_type_match(type1, type2):
    """Check if transaction types match"""
    if not type1 or not type2:
        return False
    
    type1 = type1.lower()
    type2 = type2.lower()
    
    # Direct match
    if type1 == type2:
        return True
    
    # Check if one contains the other
    if type1 in type2 or type2 in type1:
        return True
    
    # Common equivalents
    equivalents = {
        'acquisition': ['merger', 'buyout', 'm&a'],
        'ipo': ['public offering', 'going public'],
        'seed': ['pre-seed', 'angel'],
        'series a': ['round a', 'a round'],
        'series b': ['round b', 'b round'],
        'series c': ['round c', 'c round']
    }
    
    for key, values in equivalents.items():
        if key in type1:
            for val in values:
                if val in type2:
                    return True
        if key in type2:
            for val in values:
                if val in type1:
                    return True
    
    return False

if __name__ == "__main__":
    improved_two_pass_analysis()