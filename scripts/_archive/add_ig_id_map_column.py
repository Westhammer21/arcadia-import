#!/usr/bin/env python3
"""
Add IG_ID_MAP column to arcadia_new.csv
========================================
Adds a column for manual mapping to InvestGame IDs

Author: Data Analytics Team
Date: 02-09-2025
"""

import pandas as pd

def add_mapping_column():
    """Add IG_ID_MAP column to arcadia_new.csv"""
    print("\nAdding IG_ID_MAP column to arcadia_new.csv...")
    print("-" * 60)
    
    # Load the file
    df = pd.read_csv('output/arcadia_new.csv', encoding='utf-8')
    print(f"Loaded {len(df)} transactions")
    
    # Add the new column at the beginning (after ID column)
    # Initialize with empty strings for manual filling
    df.insert(1, 'IG_ID_MAP', '')
    
    # Save the updated file
    df.to_csv('output/arcadia_new.csv', index=False, encoding='utf-8')
    print(f"[SUCCESS] Added IG_ID_MAP column to arcadia_new.csv")
    print(f"Column position: 2nd column (after ID)")
    print(f"Initial values: Empty (ready for manual mapping)")
    
    return df

if __name__ == "__main__":
    df = add_mapping_column()
    print(f"\nFile ready for manual mapping: output/arcadia_new.csv")