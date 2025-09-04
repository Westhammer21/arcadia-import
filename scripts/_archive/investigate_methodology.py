import pandas as pd
import numpy as np
import re
from collections import Counter

print("=" * 80)
print("METHODOLOGY INVESTIGATION - UNDERSTANDING THE DATA")
print("=" * 80)

# Load the test_description_full.csv to analyze what we actually have
df = pd.read_csv('../output/test_description_full.csv', encoding='utf-8')
print(f"\nLoaded {len(df)} records from test_description_full.csv")

# ============================================================================
# INVESTIGATE ORIGINAL VS STANDARDIZED DESCRIPTIONS
# ============================================================================

print("\n1. ANALYZING ORIGINAL DATA CHARACTERISTICS:")
print("-" * 60)

# Check for HTML patterns in original descriptions
def analyze_html_patterns(series, name):
    """Analyze HTML patterns in descriptions"""
    html_tags = []
    html_entities = []
    
    for text in series.dropna():
        text = str(text)
        # Find HTML tags
        tags = re.findall(r'<[^>]+>', text)
        html_tags.extend(tags)
        # Find HTML entities
        entities = re.findall(r'&[a-z]+;|&#\d+;', text)
        html_entities.extend(entities)
    
    print(f"\n   {name}:")
    print(f"   - Records with data: {series.notna().sum()}/{len(series)}")
    print(f"   - Unique HTML tags found: {len(set(html_tags))}")
    if html_tags:
        tag_counts = Counter(html_tags)
        print(f"     Most common tags: {list(tag_counts.most_common(5))}")
    print(f"   - Unique HTML entities found: {len(set(html_entities))}")
    if html_entities:
        entity_counts = Counter(html_entities)
        print(f"     Most common entities: {list(entity_counts.most_common(5))}")

# Analyze both original columns
analyze_html_patterns(df['IG_Description_Original'], 'IG Original Descriptions')
analyze_html_patterns(df['ARC_Description_Original'], 'ARC Original Descriptions')

# ============================================================================
# ANALYZE CURRENCY PATTERNS
# ============================================================================

print("\n2. CURRENCY PATTERN ANALYSIS:")
print("-" * 60)

def analyze_currency_patterns(series, name):
    """Analyze currency patterns in descriptions"""
    patterns = {
        'USD_millions': r'\$\d+(?:\.\d+)?[mM](?:illion)?',
        'USD_billions': r'\$\d+(?:\.\d+)?[bB](?:illion)?',
        'GBP_symbol': r'£\d+(?:\.\d+)?[mMbB]?',
        'GBP_text': r'GBP\s*\d+(?:\.\d+)?[mMbB]?',
        'EUR_symbol': r'€\d+(?:\.\d+)?[mMbB]?',
        'EUR_text': r'EUR\s*\d+(?:\.\d+)?[mMbB]?',
    }
    
    print(f"\n   {name}:")
    for pattern_name, pattern in patterns.items():
        matches = []
        for text in series.dropna():
            found = re.findall(pattern, str(text), re.IGNORECASE)
            matches.extend(found)
        if matches:
            print(f"   - {pattern_name}: {len(matches)} instances")
            print(f"     Examples: {matches[:3]}")

analyze_currency_patterns(df['IG_Description_Original'], 'IG Descriptions')
analyze_currency_patterns(df['ARC_Description_Original'], 'ARC Descriptions')

# ============================================================================
# ANALYZE LENGTH DISTRIBUTIONS
# ============================================================================

print("\n3. LENGTH DISTRIBUTION ANALYSIS:")
print("-" * 60)

def analyze_lengths(orig_col, std_col, name):
    """Compare original vs standardized lengths"""
    orig_lengths = [len(str(x)) for x in orig_col if pd.notna(x)]
    std_lengths = [len(str(x)) for x in std_col if pd.notna(x) and str(x) != '']
    
    if orig_lengths and std_lengths:
        print(f"\n   {name}:")
        print(f"   Original - Mean: {np.mean(orig_lengths):.0f}, Median: {np.median(orig_lengths):.0f}, Max: {max(orig_lengths)}")
        print(f"   Standardized - Mean: {np.mean(std_lengths):.0f}, Median: {np.median(std_lengths):.0f}, Max: {max(std_lengths)}")
        print(f"   Average reduction: {(np.mean(orig_lengths) - np.mean(std_lengths)):.0f} chars")

analyze_lengths(df['IG_Description_Original'], df['IG_Description_Standardized'], 'IG Descriptions')
analyze_lengths(df['ARC_Description_Original'], df['ARC_Description_Standardized'], 'ARC Descriptions')

# ============================================================================
# ANALYZE STANDARDIZATION IMPACT
# ============================================================================

print("\n4. STANDARDIZATION IMPACT ANALYSIS:")
print("-" * 60)

# Check how many descriptions changed
ig_changed = 0
arc_changed = 0

for idx, row in df.iterrows():
    if pd.notna(row['IG_Description_Original']) and pd.notna(row['IG_Description_Standardized']):
        if str(row['IG_Description_Original']).strip() != str(row['IG_Description_Standardized']).strip():
            ig_changed += 1
    if pd.notna(row['ARC_Description_Original']) and pd.notna(row['ARC_Description_Standardized']):
        if str(row['ARC_Description_Original']).strip() != str(row['ARC_Description_Standardized']).strip():
            arc_changed += 1

print(f"   IG descriptions changed by standardization: {ig_changed}/{df['IG_Description_Original'].notna().sum()} ({ig_changed/df['IG_Description_Original'].notna().sum()*100:.1f}%)")
print(f"   ARC descriptions changed by standardization: {arc_changed}/{df['ARC_Description_Original'].notna().sum()} ({arc_changed/df['ARC_Description_Original'].notna().sum()*100:.1f}%)")

# ============================================================================
# ANALYZE COMMON DIFFERENCES
# ============================================================================

print("\n5. COMMON STANDARDIZATION TRANSFORMATIONS:")
print("-" * 60)

# Sample some transformations
samples = []
for idx, row in df.head(500).iterrows():
    orig = str(row['ARC_Description_Original']) if pd.notna(row['ARC_Description_Original']) else ''
    std = str(row['ARC_Description_Standardized']) if pd.notna(row['ARC_Description_Standardized']) else ''
    
    if orig and std and orig != std:
        # Look for specific transformations
        if '£' in orig and 'GBP' in std:
            samples.append(('GBP conversion', orig[:50], std[:50]))
        elif '<p>' in orig and '<p>' not in std:
            samples.append(('HTML removal', orig[:50], std[:50]))
        elif '&amp;' in orig and '&' in std:
            samples.append(('Entity decode', orig[:50], std[:50]))
        
        if len(samples) >= 5:
            break

print("   Sample transformations:")
for transform_type, orig, std in samples:
    print(f"\n   {transform_type}:")
    print(f"   Original: {orig}...")
    print(f"   Standard: {std}...")

# ============================================================================
# ANALYZE SIMILARITY DISTRIBUTION
# ============================================================================

print("\n6. SIMILARITY SCORE DISTRIBUTION:")
print("-" * 60)

# Analyze the similarity scores
similarity_scores = df[df['Overall_Similarity'] > 0]['Overall_Similarity']

print(f"   Total comparable records: {len(similarity_scores)}")
print(f"   Score distribution:")
print(f"   - 100% (exact): {(similarity_scores == 100).sum()}")
print(f"   - 95-99%: {((similarity_scores >= 95) & (similarity_scores < 100)).sum()}")
print(f"   - 90-94%: {((similarity_scores >= 90) & (similarity_scores < 95)).sum()}")
print(f"   - 80-89%: {((similarity_scores >= 80) & (similarity_scores < 90)).sum()}")
print(f"   - 70-79%: {((similarity_scores >= 70) & (similarity_scores < 80)).sum()}")
print(f"   - 50-69%: {((similarity_scores >= 50) & (similarity_scores < 70)).sum()}")
print(f"   - <50%: {(similarity_scores < 50).sum()}")

# ============================================================================
# ANALYZE MISMATCHES
# ============================================================================

print("\n7. ANALYZING LOW SIMILARITY CASES:")
print("-" * 60)

# Get low similarity cases
low_sim = df[(df['Overall_Similarity'] > 0) & (df['Overall_Similarity'] < 50)]
print(f"   Found {len(low_sim)} cases with <50% similarity")

if len(low_sim) > 0:
    # Analyze patterns in mismatches
    print("\n   Common patterns in mismatches:")
    
    for idx, row in low_sim.head(10).iterrows():
        ig_desc = str(row['IG_Description_Standardized'])[:100] if pd.notna(row['IG_Description_Standardized']) else ''
        arc_desc = str(row['ARC_Description_Standardized'])[:100] if pd.notna(row['ARC_Description_Standardized']) else ''
        
        # Check for specific mismatch patterns
        if 'raised' in ig_desc.lower() and 'acquired' in arc_desc.lower():
            print(f"   - Different transaction type (funding vs acquisition)")
        elif '$' in ig_desc and '$' in arc_desc:
            ig_amount = re.findall(r'\$\d+(?:\.\d+)?', ig_desc)
            arc_amount = re.findall(r'\$\d+(?:\.\d+)?', arc_desc)
            if ig_amount and arc_amount and ig_amount[0] != arc_amount[0]:
                print(f"   - Different amounts ({ig_amount[0]} vs {arc_amount[0]})")
        elif len(ig_desc) > 50 and len(arc_desc) < 20:
            print(f"   - Length mismatch (detailed vs brief)")

# ============================================================================
# RECOMMENDATIONS
# ============================================================================

print("\n" + "=" * 80)
print("METHODOLOGY RECOMMENDATIONS")
print("=" * 80)

print("\n1. CURRENT APPROACH EVALUATION:")
print("   Strengths:")
print("   - HTML cleaning is necessary (309 ARC descriptions have HTML)")
print("   - Currency normalization helps (£ vs GBP issue)")
print("   - Entity decoding is important (&amp; etc.)")

print("\n   Potential Improvements:")
print("   - Consider fuzzy matching for company names")
print("   - Add special handling for transaction type keywords")
print("   - Implement amount extraction and comparison")
print("   - Use semantic similarity for better context understanding")

print("\n2. ALTERNATIVE APPROACHES TO CONSIDER:")
print("   a) Token-based with keyword extraction")
print("   b) Semantic embedding similarity (using sentence transformers)")
print("   c) Structured extraction (company, amount, type) then compare")
print("   d) Multi-level matching (exact -> fuzzy -> semantic)")

print("\n" + "=" * 80)