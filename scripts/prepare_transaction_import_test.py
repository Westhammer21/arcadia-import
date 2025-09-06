#!/usr/bin/env python3

import pandas as pd
import sys
import os

def prepare_transaction_import_test(test_size=50):
    """
    Prepare InvestGame unmapped transactions for Arcadia import
    Start with test batch, then process all if successful
    """
    
    print(f"=== Transaction Import Preparation - Test Batch ({test_size} transactions) ===")
    
    # Load source files
    print("Loading source files...")
    
    # Load unmapped transactions
    transactions_df = pd.read_csv('output/ig_arc_unmapped_vF.csv')
    print(f"Loaded {len(transactions_df)} unmapped transactions")
    
    # Load company data with IG_ID mappings
    companies_df = pd.read_csv('output/arcadia_company_unmapped.csv')
    print(f"Loaded {len(companies_df)} company records")
    
    # Take test batch of transactions
    test_transactions = transactions_df.head(test_size).copy()
    print(f"Processing test batch of {len(test_transactions)} transactions")
    
    # Create company ID mapping for TO BE CREATED companies
    tbc_companies = companies_df[companies_df['status'] == 'TO BE CREATED'].copy()
    print(f"Found {len(tbc_companies)} companies with TO BE CREATED status")
    
    # Assign [Number]TBC IDs to TO BE CREATED companies
    tbc_id_mapping = {}
    for idx, (_, company) in enumerate(tbc_companies.iterrows(), 1):
        tbc_id = f"[{idx}]TBC"
        tbc_id_mapping[company['IG_ID']] = tbc_id
    
    print(f"Created {len(tbc_id_mapping)} [Number]TBC ID mappings")
    
    # Create transaction cards
    transaction_cards = []
    
    for idx, transaction in test_transactions.iterrows():
        # Base transaction data (using pandas index as transaction ID)
        card = {
            'TRANSACTION_ID': f"IG_{idx}",  # Using pandas index as ID
            'DATE': transaction.get('Date', ''),
            'AMOUNT': transaction.get('Size, $m', ''),
            'ROUND': transaction.get('Mapped_Type', ''),
            'CATEGORY': transaction.get('Mapped_Category', ''),
            'STATUS': 'IMPORTED',
            'SOURCE': 'InvestGame',
            'ORIGINAL_IG_INDEX': idx,
            'TARGET_NAME': transaction.get('Target name', ''),
            'INVESTORS_BUYERS': transaction.get('Investors / Buyers', ''),
            'IG_ID': transaction.get('IG_ID', '')
        }
        
        # Get target company
        target_companies = companies_df[
            (companies_df['IG_ID'] == transaction['IG_ID']) & 
            (companies_df['ig_role'] == 'target')
        ]
        
        if not target_companies.empty:
            target = target_companies.iloc[0]
            if target['status'] == 'TO BE CREATED':
                card['TARGET_COMPANY_ID'] = tbc_id_mapping.get(target['IG_ID'], target['IG_ID'])
            else:
                card['TARGET_COMPANY_ID'] = target.get('id', target['IG_ID'])
            card['TARGET_COMPANY_NAME'] = target.get('name', '')
        else:
            # Fallback to transaction data if no target company mapping found
            card['TARGET_COMPANY_ID'] = f"MISSING_TARGET_{transaction.get('IG_ID', idx)}"
            card['TARGET_COMPANY_NAME'] = transaction.get('Target name', '')
        
        # Get investor companies
        investor_companies = companies_df[
            (companies_df['IG_ID'] == transaction['IG_ID']) & 
            (companies_df['ig_role'].isin(['investor', 'lead', 'participant']))
        ]
        
        investors = []
        for _, investor in investor_companies.iterrows():
            investor_data = {
                'role': investor['ig_role'],
                'name': investor.get('name', ''),
            }
            
            if investor['status'] == 'TO BE CREATED':
                investor_data['id'] = tbc_id_mapping.get(investor['IG_ID'], investor['IG_ID'])
            else:
                investor_data['id'] = investor.get('id', investor['IG_ID'])
                
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
    
    print(f"\n=== Test Batch Results ===")
    print(f"Processed {len(cards_df)} transaction cards")
    print(f"Saved to: {output_file}")
    print(f"TO BE CREATED mappings: {len(tbc_id_mapping)}")
    
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
    
    # Summary statistics
    tbc_transactions = sum(1 for card in transaction_cards 
                          if any(card.get(f'INVESTOR_{i}_ID', '').endswith('TBC') 
                                for i in range(1, card.get('INVESTORS_COUNT', 0) + 1))
                          or card.get('TARGET_COMPANY_ID', '').endswith('TBC'))
    
    missing_targets = sum(1 for card in transaction_cards 
                         if card.get('TARGET_COMPANY_ID', '').startswith('MISSING_TARGET'))
    
    print(f"\n=== Summary Statistics ===")
    print(f"Total transactions processed: {len(cards_df)}")
    print(f"Transactions with TO BE CREATED companies: {tbc_transactions}")
    print(f"Transactions with missing target mappings: {missing_targets}")
    print(f"All transactions assigned status: IMPORTED")
    
    return output_file, len(cards_df), len(tbc_id_mapping)

if __name__ == "__main__":
    try:
        # Run test with 50 transactions
        output_file, processed_count, tbc_count = prepare_transaction_import_test(50)
        print(f"\n[SUCCESS] Test batch completed successfully!")
        print(f"Output file: {output_file}")
        print(f"Ready to process all 882 transactions if test results look good.")
        
    except Exception as e:
        print(f"[ERROR] Failed to process transaction import test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)