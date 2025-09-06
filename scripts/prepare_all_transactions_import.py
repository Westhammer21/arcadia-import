#!/usr/bin/env python3

import pandas as pd
import sys
import os
import re

def prepare_all_transactions_import():
    """
    Prepare ALL InvestGame unmapped transactions for Arcadia import
    Create company cards directly from transaction data with [Number]TBC IDs
    """
    
    print(f"=== Complete Transaction Import Preparation - All 882 Transactions ===")
    
    # Load source files
    print("Loading source files...")
    
    # Load unmapped transactions
    transactions_df = pd.read_csv('output/ig_arc_unmapped_vF.csv')
    print(f"Loaded {len(transactions_df)} unmapped transactions")
    
    # Create transaction cards and collect companies
    transaction_cards = []
    company_cards = {}
    tbc_counter = 1
    
    def get_or_create_company_id(name, role):
        nonlocal tbc_counter
        
        # Create a key for the company
        company_key = f"{name}_{role}".lower().strip()
        
        if company_key not in company_cards:
            # Create new company card with [Number]TBC ID
            company_id = f"[{tbc_counter}]TBC"
            company_cards[company_key] = {
                'id': company_id,
                'name': name,
                'role': role,
                'status': 'TO BE CREATED'
            }
            tbc_counter += 1
            return company_id
        
        return company_cards[company_key]['id']
    
    print("Processing all transactions...")
    
    for idx, transaction in transactions_df.iterrows():
        # Base transaction data
        card = {
            'TRANSACTION_ID': f"IG_{idx}",
            'DATE': transaction.get('Date', ''),
            'AMOUNT': transaction.get('Size, $m', ''),
            'ROUND': transaction.get('Mapped_Type', ''),
            'CATEGORY': transaction.get('Mapped_Category', ''),
            'STATUS': 'IMPORTED',
            'SOURCE': 'InvestGame',
            'ORIGINAL_IG_INDEX': idx,
            'ORIGINAL_IG_ID': transaction.get('IG_ID', ''),
        }
        
        # Process target company
        target_raw = transaction.get('Target name', '')
        target_name = str(target_raw).strip() if pd.notna(target_raw) else ''
        if target_name:
            card['TARGET_COMPANY_ID'] = get_or_create_company_id(target_name, 'target')
            card['TARGET_COMPANY_NAME'] = target_name
        else:
            card['TARGET_COMPANY_ID'] = f"[{tbc_counter}]TBC"
            card['TARGET_COMPANY_NAME'] = f"Unknown Target {idx}"
            tbc_counter += 1
        
        # Process investors/buyers
        investors_raw = transaction.get('Investors / Buyers', '')
        investors_text = str(investors_raw).strip() if pd.notna(investors_raw) else ''
        investors = []
        
        if investors_text and investors_text.lower() not in ['undisclosed', 'n/a', 'na', '']:
            # Parse investors - split by common delimiters
            investor_names = re.split(r'[,;/&+]|\s+and\s+', investors_text)
            investor_names = [name.strip() for name in investor_names if name.strip()]
            
            for i, investor_name in enumerate(investor_names):
                # Assign roles: first investor is lead, others are participants
                role = 'lead' if i == 0 else 'participant'
                
                investor_data = {
                    'id': get_or_create_company_id(investor_name, role),
                    'name': investor_name,
                    'role': role
                }
                investors.append(investor_data)
        else:
            # Handle undisclosed investors
            investor_data = {
                'id': get_or_create_company_id('Undisclosed', 'lead'),
                'name': 'Undisclosed',
                'role': 'lead'
            }
            investors.append(investor_data)
        
        # Add investor information to card
        card['INVESTORS_COUNT'] = len(investors)
        for i, investor in enumerate(investors):
            card[f'INVESTOR_{i+1}_ID'] = investor['id']
            card[f'INVESTOR_{i+1}_NAME'] = investor['name']
            card[f'INVESTOR_{i+1}_ROLE'] = investor['role']
        
        transaction_cards.append(card)
        
        # Progress indicator
        if (idx + 1) % 100 == 0:
            print(f"  Processed {idx + 1}/{len(transactions_df)} transactions...")
    
    print("Creating output files...")
    
    # Convert to DataFrame
    cards_df = pd.DataFrame(transaction_cards)
    
    # Save all transactions
    output_file = 'output/transaction_import_FINAL_ALL.csv'
    cards_df.to_csv(output_file, index=False)
    
    # Save company cards created
    companies_list = []
    for company_key, company_data in company_cards.items():
        companies_list.append(company_data)
    
    companies_df = pd.DataFrame(companies_list)
    companies_output = 'output/companies_import_FINAL_ALL.csv'
    companies_df.to_csv(companies_output, index=False)
    
    print(f"\n=== FINAL RESULTS ===")
    print(f"Processed {len(cards_df)} transaction cards")
    print(f"Created {len(company_cards)} unique companies")
    print(f"Saved transactions to: {output_file}")
    print(f"Saved companies to: {companies_output}")
    
    # Summary statistics
    target_count = len([c for c in company_cards.values() if c['role'] == 'target'])
    lead_count = len([c for c in company_cards.values() if c['role'] == 'lead'])
    participant_count = len([c for c in company_cards.values() if c['role'] == 'participant'])
    
    print(f"\n=== FINAL SUMMARY STATISTICS ===")
    print(f"Total transactions processed: {len(cards_df)}")
    print(f"Total companies created: {len(company_cards)}")
    print(f"  - Target companies: {target_count}")
    print(f"  - Lead investors: {lead_count}")
    print(f"  - Participant investors: {participant_count}")
    print(f"All transactions assigned status: IMPORTED")
    print(f"All companies assigned status: TO BE CREATED")
    
    # Show transaction type distribution
    print(f"\n=== TRANSACTION TYPE DISTRIBUTION ===")
    type_counts = cards_df['ROUND'].value_counts()
    for round_type, count in type_counts.head(10).items():
        print(f"  {round_type}: {count}")
    
    # Show category distribution  
    print(f"\n=== CATEGORY DISTRIBUTION ===")
    category_counts = cards_df['CATEGORY'].value_counts()
    for category, count in category_counts.items():
        print(f"  {category}: {count}")
    
    return output_file, companies_output, len(cards_df), len(company_cards)

if __name__ == "__main__":
    try:
        # Process all 882 transactions
        trans_file, comp_file, trans_count, comp_count = prepare_all_transactions_import()
        print(f"\n[SUCCESS] Complete import preparation finished!")
        print(f"Transaction file: {trans_file}")
        print(f"Company file: {comp_file}")
        print(f"Ready for Arcadia import!")
        
    except Exception as e:
        print(f"[ERROR] Failed to process complete transaction import: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)