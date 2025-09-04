"""
Intelligent Financial Analyst Verification Script
================================================
Author: Senior Financial Analyst - Gaming & Entertainment Sector
Date: 2025-01-02
Version: 1.0

This script performs intelligent verification of potential duplicate transactions
using domain knowledge of gaming/entertainment companies, M&A patterns, and
financial transaction characteristics.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
import json
import warnings
warnings.filterwarnings('ignore')

class FinancialAnalystVerifier:
    """
    Intelligent financial analyst for gaming/entertainment transaction verification
    """
    
    def __init__(self):
        """Initialize with domain knowledge"""
        
        # Known company relationships and acquisitions in gaming industry
        self.known_acquisitions = {
            'tencent': ['riot games', 'supercell', 'epic games', 'grinding gear games'],
            'microsoft': ['activision blizzard', 'bethesda', 'mojang', 'ninja theory'],
            'sony': ['bungie', 'insomniac games', 'naughty dog', 'firewalk studios'],
            'embracer group': ['gearbox', 'crystal dynamics', 'eidos montreal', 'dark horse'],
            'take-two': ['zynga', 'rockstar games', '2k games'],
            'ea': ['respawn', 'codemasters', 'dice', 'bioware'],
            'unity': ['weta digital', 'parsec', 'vivox'],
            'epic games': ['psyonix', 'harmonix', 'mediatonic']
        }
        
        # Known rebrands and name changes
        self.known_rebrands = {
            'facebook': 'meta',
            'thq nordic': 'embracer group',
            'activision': 'activision blizzard',
            'square enix': ['square', 'enix'],
            'bandai namco': ['bandai', 'namco'],
            'warner bros games': ['wb games', 'warner bros interactive']
        }
        
        # Common investor patterns in gaming
        self.gaming_investors = {
            'vc_gaming_specialists': [
                'andreessen horowitz', 'a16z', 'galaxy interactive', 'makers fund',
                'bitkraft ventures', 'play ventures', 'konvoy ventures', 'griffin gaming partners'
            ],
            'strategic_gaming': [
                'tencent', 'netease', 'sony', 'microsoft', 'nintendo',
                'take-two', 'ea', 'ubisoft', 'embracer'
            ],
            'general_tech_vc': [
                'sequoia', 'accel', 'benchmark', 'index ventures', 'lightspeed'
            ]
        }
        
        # Transaction type patterns
        self.transaction_patterns = {
            'talent_acquisition': {
                'size_range': (1, 50),  # Usually small
                'common_acquirers': ['facebook', 'google', 'amazon', 'apple']
            },
            'strategic_acquisition': {
                'size_range': (50, 500),
                'indicators': ['technology', 'ip', 'user base']
            },
            'mega_deal': {
                'size_range': (500, 100000),
                'requires_regulatory': True
            }
        }
        
        # Known problematic data patterns
        self.data_issues = {
            'announcement_vs_closing': 180,  # Days between announcement and closing
            'subsidiary_recording': True,  # Same deal recorded for parent and subsidiary
            'tranches': True,  # Single round recorded as multiple transactions
            'regional_differences': True  # Same deal different amounts in different currencies
        }
    
    def analyze_transaction_pair(self, ig_record, arc_record, initial_confidence=None):
        """
        Perform intelligent analysis of a potential duplicate pair
        
        Returns detailed analysis with:
        - is_duplicate: Boolean
        - adjusted_confidence: Updated confidence based on analysis
        - reasoning: Detailed explanation
        - red_flags: Any concerning patterns
        - recommendation: Action to take
        """
        
        analysis = {
            'is_duplicate': False,
            'initial_confidence': initial_confidence,
            'adjusted_confidence': 0,
            'reasoning': [],
            'red_flags': [],
            'green_flags': [],
            'recommendation': '',
            'analyst_notes': []
        }
        
        # Extract key fields
        ig_target = str(ig_record.get('Target name', '')).lower()
        arc_target = str(arc_record.get('Target Company', '')).lower()
        
        ig_date = pd.to_datetime(ig_record.get('Date'))
        arc_date = pd.to_datetime(arc_record.get('Announcement date*'))
        date_diff = abs((arc_date - ig_date).days)
        
        ig_size = float(ig_record.get('Size, $m', 0) or 0)
        arc_size = float(arc_record.get('Transaction Size*, $M', 0) or 0)
        
        ig_type = str(ig_record.get('Final_Type', '')).lower()
        arc_type = str(arc_record.get('Transaction Type*', '')).lower()
        
        ig_category = str(ig_record.get('Final_Category', ''))
        arc_category = str(arc_record.get('Transaction Category*', ''))
        
        # 1. Analyze company names with domain knowledge
        name_analysis = self._analyze_names(ig_target, arc_target)
        
        # 2. Analyze transaction characteristics
        transaction_analysis = self._analyze_transaction_characteristics(
            ig_size, arc_size, ig_type, arc_type, ig_category, arc_category
        )
        
        # 3. Analyze temporal patterns
        temporal_analysis = self._analyze_temporal_patterns(
            ig_date, arc_date, date_diff, ig_type, ig_size
        )
        
        # 4. Check for known patterns
        pattern_analysis = self._check_known_patterns(
            ig_target, arc_target, ig_size, arc_size, date_diff
        )
        
        # 5. Synthesize analysis
        total_score = 0
        max_score = 0
        
        # Name matching (40 points max)
        if name_analysis['exact_match']:
            total_score += 40
            analysis['green_flags'].append("Exact name or known alias match")
        elif name_analysis['parent_subsidiary']:
            total_score += 35
            analysis['green_flags'].append("Parent/subsidiary relationship identified")
        elif name_analysis['known_rebrand']:
            total_score += 35
            analysis['green_flags'].append("Known rebrand/name change")
        elif name_analysis['similarity'] >= 90:
            total_score += 30
            analysis['green_flags'].append(f"Very high name similarity ({name_analysis['similarity']}%)")
        elif name_analysis['similarity'] >= 80:
            total_score += 20
            analysis['reasoning'].append(f"Good name similarity ({name_analysis['similarity']}%)")
        elif name_analysis['similarity'] >= 70:
            total_score += 10
            analysis['reasoning'].append(f"Moderate name similarity ({name_analysis['similarity']}%)")
        else:
            analysis['red_flags'].append(f"Low name similarity ({name_analysis['similarity']}%)")
        max_score += 40
        
        # Transaction characteristics (30 points max)
        if transaction_analysis['size_match']:
            total_score += 15
            analysis['green_flags'].append("Transaction sizes match")
        elif transaction_analysis['size_explainable']:
            total_score += 10
            analysis['reasoning'].append(transaction_analysis['size_explanation'])
        else:
            analysis['red_flags'].append("Significant unexplained size difference")
        
        if transaction_analysis['type_match']:
            total_score += 10
            analysis['green_flags'].append("Transaction types align")
        
        if transaction_analysis['category_compatible']:
            total_score += 5
            analysis['reasoning'].append("Categories are compatible")
        max_score += 30
        
        # Temporal patterns (20 points max)
        if temporal_analysis['date_match']:
            total_score += 20
            analysis['green_flags'].append(f"Dates align well ({date_diff} days)")
        elif temporal_analysis['explainable_delay']:
            total_score += 15
            analysis['reasoning'].append(temporal_analysis['delay_explanation'])
        elif date_diff <= 90:
            total_score += 10
            analysis['reasoning'].append(f"Dates reasonably close ({date_diff} days)")
        else:
            analysis['red_flags'].append(f"Large date discrepancy ({date_diff} days)")
        max_score += 20
        
        # Known patterns (10 points max)
        if pattern_analysis['known_deal']:
            total_score += 10
            analysis['green_flags'].append("Matches known industry deal pattern")
        elif pattern_analysis['suspicious']:
            analysis['red_flags'].append(pattern_analysis['suspicion_reason'])
        max_score += 10
        
        # Calculate final confidence
        confidence_score = (total_score / max_score) * 100
        
        # Determine if duplicate
        if confidence_score >= 75:
            analysis['is_duplicate'] = True
            analysis['adjusted_confidence'] = min(100, int(confidence_score))
            analysis['recommendation'] = "HIGH CONFIDENCE - Merge records"
        elif confidence_score >= 60:
            analysis['is_duplicate'] = True
            analysis['adjusted_confidence'] = 75
            analysis['recommendation'] = "PROBABLE - Recommend merge with manual review"
        elif confidence_score >= 50:
            analysis['is_duplicate'] = False
            analysis['adjusted_confidence'] = 50
            analysis['recommendation'] = "UNCERTAIN - Requires detailed manual investigation"
        else:
            analysis['is_duplicate'] = False
            analysis['adjusted_confidence'] = min(40, int(confidence_score))
            analysis['recommendation'] = "UNLIKELY - Keep as separate records"
        
        # Add analyst summary
        self._add_analyst_summary(analysis, ig_record, arc_record)
        
        return analysis
    
    def _analyze_names(self, name1, name2):
        """Analyze company names using domain knowledge"""
        result = {
            'exact_match': False,
            'parent_subsidiary': False,
            'known_rebrand': False,
            'similarity': 0
        }
        
        # Check exact match
        if name1 == name2:
            result['exact_match'] = True
            result['similarity'] = 100
            return result
        
        # Check known acquisitions
        for parent, subsidiaries in self.known_acquisitions.items():
            if parent in name1 and any(sub in name2 for sub in subsidiaries):
                result['parent_subsidiary'] = True
                result['similarity'] = 85
                return result
            if parent in name2 and any(sub in name1 for sub in subsidiaries):
                result['parent_subsidiary'] = True
                result['similarity'] = 85
                return result
        
        # Check known rebrands
        for old_name, new_name in self.known_rebrands.items():
            if isinstance(new_name, list):
                if any(n in name1 for n in new_name) and old_name in name2:
                    result['known_rebrand'] = True
                    result['similarity'] = 90
                    return result
            else:
                if old_name in name1 and new_name in name2:
                    result['known_rebrand'] = True
                    result['similarity'] = 90
                    return result
                if old_name in name2 and new_name in name1:
                    result['known_rebrand'] = True
                    result['similarity'] = 90
                    return result
        
        # Fuzzy matching
        result['similarity'] = fuzz.ratio(name1, name2)
        
        # Check for common gaming terms that might cause false matches
        gaming_terms = ['games', 'studio', 'interactive', 'entertainment', 'digital', 'mobile']
        for term in gaming_terms:
            if term in name1 and term in name2:
                # Reduce similarity if only matching on generic terms
                name1_clean = name1.replace(term, '').strip()
                name2_clean = name2.replace(term, '').strip()
                if fuzz.ratio(name1_clean, name2_clean) < 50:
                    result['similarity'] = min(result['similarity'], 60)
        
        return result
    
    def _analyze_transaction_characteristics(self, size1, size2, type1, type2, cat1, cat2):
        """Analyze transaction characteristics"""
        result = {
            'size_match': False,
            'size_explainable': False,
            'size_explanation': '',
            'type_match': False,
            'category_compatible': False
        }
        
        # Size analysis
        if size1 == 0 and size2 == 0:
            result['size_match'] = True
        elif size1 == 0 or size2 == 0:
            result['size_explainable'] = True
            result['size_explanation'] = "One transaction undisclosed (common in private deals)"
        elif size1 > 0 and size2 > 0:
            size_ratio = min(size1, size2) / max(size1, size2)
            if size_ratio >= 0.9:  # Within 10%
                result['size_match'] = True
            elif size_ratio >= 0.75:  # Within 25%
                result['size_explainable'] = True
                result['size_explanation'] = "Size difference could be exchange rate or reporting variation"
            elif abs(size1 - size2) <= 5:  # Within $5M
                result['size_match'] = True
            
            # Check for known patterns
            if size1 / size2 in [0.5, 2.0]:  # Exactly half or double
                result['size_explainable'] = True
                result['size_explanation'] = "Size is exactly half/double - possible tranche or partial reporting"
        
        # Type matching
        type_equivalents = {
            'acquisition': ['merger', 'buyout', 'm&a', 'acquired'],
            'seed': ['pre-seed', 'angel', 'seed round'],
            'series a': ['a round', 'round a'],
            'series b': ['b round', 'round b'],
            'series c': ['c round', 'round c'],
            'ipo': ['public offering', 'going public']
        }
        
        result['type_match'] = type1 == type2
        if not result['type_match']:
            for key, values in type_equivalents.items():
                if key in type1.lower() and any(v in type2.lower() for v in values):
                    result['type_match'] = True
                    break
        
        # Category compatibility
        compatible_categories = {
            'Early-stage Investments': ['Seed', 'Series A', 'Series B'],
            'Late-stage Investments': ['Growth / Expansion', 'Series C+'],
            'M&A': ['Merger', 'Acquisition', 'Buyout']
        }
        
        result['category_compatible'] = cat1 == cat2
        if not result['category_compatible']:
            for key, values in compatible_categories.items():
                if cat1 == key and cat2 in values:
                    result['category_compatible'] = True
                    break
        
        return result
    
    def _analyze_temporal_patterns(self, date1, date2, date_diff, trans_type, size):
        """Analyze temporal patterns in transactions"""
        result = {
            'date_match': False,
            'explainable_delay': False,
            'delay_explanation': ''
        }
        
        # Perfect match
        if date_diff <= 7:
            result['date_match'] = True
            return result
        
        # Check for typical patterns
        if date_diff <= 30:
            result['date_match'] = True
        elif date_diff <= 90:
            if 'm&a' in trans_type.lower() or 'acquisition' in trans_type.lower():
                result['explainable_delay'] = True
                result['delay_explanation'] = "M&A transactions often have long announcement-to-close periods"
            elif size > 100:  # Large deals
                result['explainable_delay'] = True
                result['delay_explanation'] = "Large deals often require regulatory approval causing delays"
        elif date_diff <= 180:
            if 'm&a' in trans_type.lower() or size > 500:
                result['explainable_delay'] = True
                result['delay_explanation'] = "Major acquisition with expected regulatory review period"
        
        # Check for quarterly reporting patterns (companies often announce at quarter end)
        if date1.month in [3, 6, 9, 12] and date2.month in [3, 6, 9, 12]:
            if date_diff <= 95:  # Same quarter different year or adjacent quarters
                result['explainable_delay'] = True
                result['delay_explanation'] = "Both dates align with quarterly reporting periods"
        
        return result
    
    def _check_known_patterns(self, target1, target2, size1, size2, date_diff):
        """Check for known industry patterns"""
        result = {
            'known_deal': False,
            'suspicious': False,
            'suspicion_reason': ''
        }
        
        # Check for known mega-deals
        known_megadeals = {
            'activision blizzard': 68700,  # Microsoft acquisition
            'zynga': 12700,  # Take-Two acquisition
            'bungie': 3600,  # Sony acquisition
            'bethesda': 7500,  # Microsoft acquisition
        }
        
        for company, deal_size in known_megadeals.items():
            if company in target1.lower() or company in target2.lower():
                if abs(size1 - deal_size) < deal_size * 0.1 or abs(size2 - deal_size) < deal_size * 0.1:
                    result['known_deal'] = True
                    return result
        
        # Check for suspicious patterns
        if size1 == size2 and size1 > 0 and date_diff > 180:
            result['suspicious'] = True
            result['suspicion_reason'] = "Identical amounts with large date gap - possible data error"
        
        if 'test' in target1.lower() or 'test' in target2.lower():
            result['suspicious'] = True
            result['suspicion_reason'] = "Test data detected"
        
        return result
    
    def _add_analyst_summary(self, analysis, ig_record, arc_record):
        """Add human-readable analyst summary"""
        
        ig_target = ig_record.get('Target name', 'Unknown')
        arc_target = arc_record.get('Target Company', 'Unknown')
        
        if analysis['is_duplicate']:
            if analysis['adjusted_confidence'] >= 90:
                summary = f"CONFIRMED DUPLICATE: {ig_target} and {arc_target} represent the same transaction. "
            elif analysis['adjusted_confidence'] >= 75:
                summary = f"PROBABLE DUPLICATE: Strong evidence that {ig_target} and {arc_target} are the same deal. "
            else:
                summary = f"POSSIBLE DUPLICATE: {ig_target} and {arc_target} show similarities. "
        else:
            summary = f"DIFFERENT TRANSACTIONS: {ig_target} and {arc_target} appear to be separate deals. "
        
        # Add key evidence
        if analysis['green_flags']:
            summary += f"Supporting evidence: {', '.join(analysis['green_flags'][:3])}. "
        
        if analysis['red_flags']:
            summary += f"Concerns: {', '.join(analysis['red_flags'][:2])}. "
        
        analysis['analyst_notes'].append(summary)
        
        # Add industry context if relevant
        ig_size = float(ig_record.get('Size, $m', 0) or 0)
        if ig_size > 1000:
            analysis['analyst_notes'].append(
                "This is a major transaction that would have been widely reported in gaming media."
            )
        
        # Check for known investor patterns
        if ig_record.get('Investors'):
            investors = str(ig_record.get('Investors', '')).lower()
            for investor_type, investor_list in self.gaming_investors.items():
                if any(inv in investors for inv in investor_list):
                    analysis['analyst_notes'].append(
                        f"Investor profile matches {investor_type.replace('_', ' ')} pattern."
                    )
                    break
    
    def verify_duplicates_batch(self, results_file, sample_size=None):
        """
        Verify a batch of potential duplicates from results file
        """
        print("="*80)
        print("INTELLIGENT FINANCIAL ANALYST VERIFICATION")
        print("="*80)
        print(f"Analyst: Senior Gaming & Entertainment Sector Specialist")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*80 + "\n")
        
        # Load results
        results_df = pd.read_csv(results_file)
        print(f"Total potential duplicates to verify: {len(results_df)}")
        
        # Load source databases from src folder
        ig_df = pd.read_csv('src/investgame_database_mapped.csv')
        ig_df['Date'] = pd.to_datetime(ig_df['Date'], format='mixed', dayfirst=True)
        
        arc_df = pd.read_csv('src/arcadia_database_with_ids.csv')
        arc_df['Announcement date*'] = pd.to_datetime(arc_df['Announcement date*'], format='mixed', dayfirst=True)
        
        # Sample if requested
        if sample_size and sample_size < len(results_df):
            # Sample across different confidence levels
            sample_dfs = []
            for conf in results_df['confidence'].unique():
                conf_df = results_df[results_df['confidence'] == conf]
                n_sample = min(int(sample_size * len(conf_df) / len(results_df)), len(conf_df))
                if n_sample > 0:
                    sample_dfs.append(conf_df.sample(n=n_sample, random_state=42))
            
            results_df = pd.concat(sample_dfs, ignore_index=True)
            print(f"Analyzing sample of {len(results_df)} transactions\n")
        
        # Perform verification
        verification_results = []
        
        for idx, row in results_df.iterrows():
            if idx % 10 == 0 and idx > 0:
                print(f"Progress: {idx}/{len(results_df)} verified...")
            
            # Get full records
            ig_record = ig_df[ig_df.index == row['ig_id']].to_dict('records')[0] if row['ig_id'] in ig_df.index.values else {}
            arc_record = arc_df[arc_df.index == row['arc_id']].to_dict('records')[0] if row['arc_id'] in arc_df.index.values else {}
            
            if not ig_record or not arc_record:
                continue
            
            # Perform intelligent analysis
            analysis = self.analyze_transaction_pair(
                ig_record, 
                arc_record, 
                initial_confidence=row.get('confidence')
            )
            
            # Store results
            verification_results.append({
                'ig_id': row['ig_id'],
                'arc_id': row['arc_id'],
                'ig_target': row['ig_target'],
                'arc_target': row['arc_target'],
                'initial_confidence': row.get('confidence'),
                'analyst_confidence': analysis['adjusted_confidence'],
                'is_duplicate': analysis['is_duplicate'],
                'recommendation': analysis['recommendation'],
                'green_flags': '; '.join(analysis['green_flags']),
                'red_flags': '; '.join(analysis['red_flags']),
                'analyst_summary': ' '.join(analysis['analyst_notes'])
            })
        
        # Save results to output folder
        output_df = pd.DataFrame(verification_results)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'output/analyst_verification_{timestamp}.csv'
        output_df.to_csv(output_file, index=False)
        
        # Print summary
        print("\n" + "="*80)
        print("VERIFICATION SUMMARY")
        print("="*80)
        
        confirmed = output_df[output_df['is_duplicate'] == True]
        rejected = output_df[output_df['is_duplicate'] == False]
        
        print(f"\nTotal analyzed: {len(output_df)}")
        print(f"Confirmed duplicates: {len(confirmed)} ({len(confirmed)/len(output_df)*100:.1f}%)")
        print(f"Rejected as duplicates: {len(rejected)} ({len(rejected)/len(output_df)*100:.1f}%)")
        
        # Confidence adjustment analysis
        print("\nConfidence Adjustments:")
        for initial_conf in sorted(output_df['initial_confidence'].unique()):
            conf_group = output_df[output_df['initial_confidence'] == initial_conf]
            avg_adjusted = conf_group['analyst_confidence'].mean()
            confirmed_pct = (conf_group['is_duplicate'].sum() / len(conf_group)) * 100
            print(f"  {initial_conf}% bucket: Avg adjusted to {avg_adjusted:.0f}%, {confirmed_pct:.0f}% confirmed")
        
        # Show sample of interesting cases
        print("\n" + "="*80)
        print("INTERESTING CASES REQUIRING ATTENTION")
        print("="*80)
        
        # Cases where confidence was significantly adjusted
        large_adjustments = output_df[
            abs(output_df['analyst_confidence'] - output_df['initial_confidence']) >= 25
        ]
        
        if len(large_adjustments) > 0:
            print("\nLarge confidence adjustments:")
            for _, row in large_adjustments.head(3).iterrows():
                print(f"\n{row['ig_target']} vs {row['arc_target']}")
                print(f"  Initial: {row['initial_confidence']}% -> Adjusted: {row['analyst_confidence']}%")
                print(f"  Reason: {row['analyst_summary'][:200]}...")
        
        print(f"\nDetailed results saved to: {output_file}")
        
        return output_df

def main():
    """Main execution"""
    verifier = FinancialAnalystVerifier()
    
    # First, run the improved duplicate detection
    print("Running improved duplicate detection algorithm v4.0...")
    from two_pass_analysis_v4 import improved_two_pass_analysis
    improved_two_pass_analysis()
    
    # Find the latest results file
    import glob
    import os
    
    results_files = glob.glob('output/two_pass_v4_results_*.csv')
    if not results_files:
        print("No results file found. Please run two_pass_analysis_v4.py first.")
        return
    
    latest_results = max(results_files, key=os.path.getctime)
    print(f"\nVerifying results from: {latest_results}")
    
    # Verify with intelligent analysis
    verification_df = verifier.verify_duplicates_batch(latest_results, sample_size=100)
    
    print("\n" + "="*80)
    print("FINANCIAL ANALYST VERIFICATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()