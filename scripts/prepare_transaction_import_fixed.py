#!/usr/bin/env python3

import pandas as pd
import sys
import os
import re

def prepare_transaction_import_test(test_size=50):
    """
    Prepare InvestGame unmapped transactions for Arcadia import
    Create company cards directly from transaction data since IG_IDs don't match
    """
    
    print(f"=== Transaction Import Preparation - Test Batch ({test_size} transactions) ===")
    
    # Load source files
    print("Loading source files...")
    
    # Load unmapped transactions
    transactions_df = pd.read_csv('output/ig_arc_unmapped_vF.csv')
    print(f"Loaded {len(transactions_df)} unmapped transactions")
    
    # Take test batch of transactions
    test_transactions = transactions_df.head(test_size).copy()
    print(f"Processing test batch of {len(test_transactions)} transactions")
    
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
    
    for idx, transaction in test_transactions.iterrows():
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
        target_name = transaction.get('Target name', '').strip()
        if target_name:
            card['TARGET_COMPANY_ID'] = get_or_create_company_id(target_name, 'target')
            card['TARGET_COMPANY_NAME'] = target_name
        else:
            card['TARGET_COMPANY_ID'] = f"[{tbc_counter}]TBC"
            card['TARGET_COMPANY_NAME'] = f"Unknown Target {idx}"
            tbc_counter += 1
        
        # Process investors/buyers
        investors_text = transaction.get('Investors / Buyers', '').strip()
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
    
    # Convert to DataFrame
    cards_df = pd.DataFrame(transaction_cards)
    
    # Save test batch
    output_file = f'output/transaction_import_test_{test_size}.csv'
    cards_df.to_csv(output_file, index=False)
    
    # Save company cards created
    companies_list = []
    for company_key, company_data in company_cards.items():
        companies_list.append(company_data)
    
    companies_df = pd.DataFrame(companies_list)
    companies_output = f'output/companies_created_test_{test_size}.csv'
    companies_df.to_csv(companies_output, index=False)
    
    print(f"\n=== Test Batch Results ===")
    print(f"Processed {len(cards_df)} transaction cards")
    print(f"Created {len(company_cards)} unique companies")
    print(f"Saved transactions to: {output_file}")
    print(f"Saved companies to: {companies_output}")
    
    # Show sample records
    print(f"\n=== Sample Transaction Cards ===")
    for i in range(min(3, len(cards_df))):
        card = cards_df.iloc[i]
        print(f"\nTransaction {i+1}:")
        print(f"  ID: {card['TRANSACTION_ID']}")
        print(f"  Target: {card.get('TARGET_COMPANY_NAME', '')} (ID: {card.get('TARGET_COMPANY_ID', '')})")
        print(f"  Amount: ${card.get('AMOUNT', 'N/A')}")
        print(f"  Round: {card.get('ROUND', '')}")
        print(f"  Investors: {card.get('INVESTORS_COUNT', 0)}")
        
        if card.get('INVESTORS_COUNT', 0) > 0:
            for j in range(int(card.get('INVESTORS_COUNT', 0))):
                inv_id = card.get(f'INVESTOR_{j+1}_ID', '')
                inv_name = card.get(f'INVESTOR_{j+1}_NAME', '')
                inv_role = card.get(f'INVESTOR_{j+1}_ROLE', '')
                print(f"    - {inv_name} ({inv_role}) ID: {inv_id}")
    
    # Show sample companies
    print(f"\n=== Sample Company Cards ===")
    sample_companies = companies_df.head(5)
    for _, company in sample_companies.iterrows():
        print(f"  {company['id']}: {company['name']} ({company['role']})")
    
    # Summary statistics
    target_count = len([c for c in company_cards.values() if c['role'] == 'target'])
    lead_count = len([c for c in company_cards.values() if c['role'] == 'lead'])
    participant_count = len([c for c in company_cards.values() if c['role'] == 'participant'])
    
    print(f"\n=== Summary Statistics ===")
    print(f"Total transactions processed: {len(cards_df)}")
    print(f"Total companies created: {len(company_cards)}")
    print(f"  - Targets: {target_count}")
    print(f"  - Leads: {lead_count}")
    print(f"  - Participants: {participant_count}")
    print(f"All transactions assigned status: IMPORTED")
    print(f"All companies assigned status: TO BE CREATED")
    
    return output_file, companies_output, len(cards_df), len(company_cards)

if __name__ == "__main__":
    try:
        # Run test with 50 transactions
        trans_file, comp_file, trans_count, comp_count = prepare_transaction_import_test(50)
        print(f"\n[SUCCESS] Test batch completed successfully!")
        print(f"Transaction file: {trans_file}")
        print(f"Company file: {comp_file}")
        print(f"Ready to process all 882 transactions if test results look good.")
        
    except Exception as e:
        print(f"[ERROR] Failed to process transaction import test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)