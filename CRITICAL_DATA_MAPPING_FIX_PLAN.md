# CRITICAL DATA MAPPING FIX PLAN
**Transaction Duplicate Detection & Mapping System**  
**Date:** September 6, 2025  
**Priority:** CRITICAL - Data Integrity Issue  
**Status:** BROKEN - Requires Immediate Fix

---

## 🚨 EXECUTIVE SUMMARY

**CRITICAL PROBLEM IDENTIFIED:** The `companies_import_FINAL_ALL.csv` file contains completely incorrect mappings that break data integrity between transactions and companies. The IG_ID to ig_role sequence mappings have been lost, making it impossible to trace which companies participated in which transactions with what roles.

**IMPACT:** 
- ❌ Complete loss of transaction-company relationships
- ❌ All company metadata stripped (25 columns reduced to 4)
- ❌ Sequential fake IDs created instead of using real IG_ID mappings
- ❌ Production import would create duplicate companies in Arcadia
- ❌ Business intelligence and reporting completely broken

**SOLUTION:** Rebuild the company import file using proper IG_ID-based mapping from the authoritative source data.

---

## 📊 CURRENT STATE ANALYSIS

### File Status Assessment

| File | Status | Records | Columns | IG_ID Mapping | Assessment |
|------|--------|---------|---------|---------------|------------|
| **ig_arc_unmapped_vF.csv** | ✅ CORRECT | 883 | 47 | Source Truth | Transactions source |
| **arcadia_company_unmapped.csv** | ✅ CORRECT | 1,537 | 25 | Preserved | Authoritative company data |
| **arcadia_company_unmapped_IMPORT_READY.csv** | ⚠️ REVIEW NEEDED | 1,537 | 25 | Preserved | May have minor issues |
| **companies_import_FINAL_ALL.csv** | ❌ BROKEN | 1,675 | 4 | LOST | Complete rebuild required |

### Critical Data Examples

#### ✅ CORRECT Mapping (arcadia_company_unmapped.csv):
```csv
id,name,IG_ID,ig_role
14.0,1Up Ventures,"73, 1176, 2155, 3248, 3975","participant, participant, participant, participant, participant"
```
**Business Logic:** 1Up Ventures participated as an investor in 5 different transactions (IG_IDs: 73, 1176, 2155, 3248, 3975), always as a participant role.

#### ❌ BROKEN Mapping (companies_import_FINAL_ALL.csv):
```csv
id,name,role,status
[1]TBC,Callisto Gaming,target,TO BE CREATED
[2]TBC,Undisclosed,lead,TO BE CREATED
```
**Problem:** Sequential fake IDs with no IG_ID relationship. Cannot trace back to source transactions.

---

## 🔍 ROOT CAUSE ANALYSIS

### The Critical Sequence Issue

**IG_ID and ig_role MUST maintain positional correspondence:**

```
Example: Animoca Brands
IG_ID: "1459, 1612, 2847"
ig_role: "lead, lead, participant"

Mapping:
- IG_ID 1459 → lead role
- IG_ID 1612 → lead role  
- IG_ID 2847 → participant role
```

**Why This Matters:**
1. **Transaction Traceability** - Each IG_ID links to a specific transaction
2. **Role Accuracy** - The company's role in each transaction must be preserved
3. **Business Intelligence** - Reporting depends on accurate company-transaction relationships
4. **Data Integrity** - One misalignment breaks the entire relationship chain

### Current Mapping Failures

1. **Sequential ID Generation**: `[1]TBC`, `[2]TBC` instead of real company IDs
2. **Lost Metadata**: 25 columns reduced to 4 basic fields
3. **Broken Relationships**: No way to trace companies back to transactions
4. **Duplicate Creation**: Same company appears multiple times with fake IDs
5. **Status Errors**: All marked "TO BE CREATED" regardless of actual status

---

## 🎯 BUSINESS LOGIC DOCUMENTATION

### Company-Transaction Relationship Model

#### Single Transaction Company
```
Company: Callisto Gaming
IG_ID: 4
ig_role: target
Business Logic: Callisto Gaming was the target company in transaction IG_ID 4
```

#### Multi-Transaction Company
```
Company: 1Up Ventures  
IG_ID: "73, 1176, 2155, 3248, 3975"
ig_role: "participant, participant, participant, participant, participant"
Business Logic: 1Up Ventures participated as an investor in 5 separate transactions
```

#### Mixed-Role Company
```
Company: Animoca Brands
IG_ID: "1459, 1612, 2847"
ig_role: "lead, lead, participant"
Business Logic: Animoca Brands led 2 transactions (1459, 1612) and participated in 1 (2847)
```

### Data Expansion Logic

For import purposes, multi-transaction companies should be expanded:

**From:**
```
1Up Ventures,"73, 1176, 2155",participant, participant, participant"
```

**To:**
```
1Up Ventures,73,participant
1Up Ventures,1176,participant  
1Up Ventures,2155,participant
```

This creates individual company-transaction records while preserving the relationship.

---

## 📋 DETAILED EXECUTION PLAN

### Phase 1: Environment Setup & Analysis (1 hour)

#### 1.1 Create Project Backup
```bash
# Create timestamped backup
mkdir "backup_$(date +%Y%m%d_%H%M%S)"
cp output/*.csv "backup_$(date +%Y%m%d_%H%M%S)/"
```

#### 1.2 Validate Source Files
- ✅ Confirm `arcadia_company_unmapped.csv` integrity (1,537 records)
- ✅ Confirm `ig_arc_unmapped_vF.csv` integrity (883 records)
- 📊 Generate file comparison report

#### 1.3 Analyze IMPORT_READY File
```python
# Check for differences between arcadia_company_unmapped.csv and IMPORT_READY version
# Document any inconsistencies or oversimplifications
```

### Phase 2: Algorithm Development (2 hours)

#### 2.1 Create Parsing Function
```python
def parse_ig_id_sequence(ig_id_str, role_str):
    """
    Parse comma-separated IG_ID and role strings maintaining sequence
    
    Args:
        ig_id_str: "73, 1176, 2155, 3248, 3975"  
        role_str: "participant, participant, participant, participant, participant"
        
    Returns:
        list: [(73, 'participant'), (1176, 'participant'), ...]
    """
    ig_ids = [id.strip() for id in ig_id_str.split(',')]
    roles = [role.strip() for role in role_str.split(',')]
    
    if len(ig_ids) != len(roles):
        raise ValueError(f"IG_ID count ({len(ig_ids)}) != role count ({len(roles)})")
    
    return list(zip(ig_ids, roles))
```

#### 2.2 Create Company Expansion Logic
```python
def expand_company_records(company_row):
    """
    Expand multi-transaction company into individual company-transaction pairs
    Preserves all metadata for each expansion
    """
    ig_id_role_pairs = parse_ig_id_sequence(company_row['IG_ID'], company_row['ig_role'])
    
    expanded_records = []
    for ig_id, role in ig_id_role_pairs:
        record = company_row.copy()
        record['IG_ID'] = ig_id
        record['ig_role'] = role
        expanded_records.append(record)
    
    return expanded_records
```

#### 2.3 Create Transaction Linkage Validation
```python
def validate_transaction_linkage(expanded_companies, transactions):
    """
    Verify every expanded company record links to valid transaction
    """
    transaction_ids = set(transactions['IG_ID'])
    company_ig_ids = set(expanded_companies['IG_ID'])
    
    missing_links = company_ig_ids - transaction_ids
    if missing_links:
        raise ValueError(f"Companies reference non-existent transactions: {missing_links}")
```

### Phase 3: Implementation (2 hours)

#### 3.1 Create Fix Script
**File:** `scripts/fix_company_import_mapping.py`

```python
#!/usr/bin/env python3
"""
Critical Data Mapping Fix Script
Rebuilds companies_import_FINAL_ALL.csv with proper IG_ID relationships
"""

import pandas as pd
import sys
from datetime import datetime

def main():
    print("🔧 Starting Critical Data Mapping Fix...")
    
    # Load source data
    print("📚 Loading source files...")
    companies = pd.read_csv('output/arcadia_company_unmapped.csv')
    transactions = pd.read_csv('output/ig_arc_unmapped_vF.csv')
    
    print(f"✅ Loaded {len(companies)} companies, {len(transactions)} transactions")
    
    # Expand multi-transaction companies
    print("🔄 Expanding multi-transaction companies...")
    expanded_records = []
    
    for _, company in companies.iterrows():
        if pd.isna(company['IG_ID']):
            continue
            
        expanded = expand_company_records(company)
        expanded_records.extend(expanded)
    
    expanded_df = pd.DataFrame(expanded_records)
    print(f"✅ Expanded to {len(expanded_df)} company-transaction pairs")
    
    # Validate linkages
    print("🔍 Validating transaction linkages...")
    validate_transaction_linkage(expanded_df, transactions)
    print("✅ All linkages validated")
    
    # Create corrected import file
    print("💾 Creating corrected import file...")
    output_file = 'output/companies_import_CORRECTED.csv'
    expanded_df.to_csv(output_file, index=False)
    
    print(f"✅ Fix completed! Corrected file: {output_file}")
    
    # Generate summary report
    generate_fix_summary(companies, expanded_df, transactions)

if __name__ == "__main__":
    main()
```

#### 3.2 Execute Fix Script
```bash
cd C:\Users\sergei\Documents\VS-Code\transactions-check
python scripts/fix_company_import_mapping.py
```

#### 3.3 Verify Output
- ✅ Confirm expanded record count matches expectations
- ✅ Verify all IG_ID relationships maintained
- ✅ Check all company metadata preserved

### Phase 4: Validation & Quality Assurance (1 hour)

#### 4.1 Sequence Integrity Tests
```python
def test_sequence_integrity():
    """Test that IG_ID to role mappings are preserved correctly"""
    # Sample test for 1Up Ventures
    ventures_records = expanded_df[expanded_df['name'] == '1Up Ventures']
    expected_pairs = [(73, 'participant'), (1176, 'participant'), (2155, 'participant'), 
                     (3248, 'participant'), (3975, 'participant')]
    
    actual_pairs = list(zip(ventures_records['IG_ID'], ventures_records['ig_role']))
    assert set(actual_pairs) == set(expected_pairs), "Sequence integrity failed"
```

#### 4.2 Transaction Coverage Validation
```python
def test_transaction_coverage():
    """Verify all transactions have corresponding company records"""
    transaction_ids = set(transactions['IG_ID'])
    company_ig_ids = set(expanded_df['IG_ID'])
    
    coverage = len(company_ig_ids) / len(transaction_ids) * 100
    print(f"Transaction coverage: {coverage:.1f}%")
    
    missing = transaction_ids - company_ig_ids
    if missing:
        print(f"⚠️ Missing company records for transactions: {missing}")
```

#### 4.3 Data Quality Verification
- ✅ No duplicate company-transaction pairs
- ✅ All required fields populated
- ✅ Status values align with business rules
- ✅ Metadata consistency maintained

---

## 🔒 RISK MITIGATION STRATEGIES

### Data Loss Prevention
1. **Automatic Backups** - All original files backed up before processing
2. **Rollback Capability** - Keep original files until validation complete
3. **Incremental Testing** - Validate each transformation step

### Quality Assurance
1. **Multi-layer Validation** - Sequence, coverage, and integrity tests
2. **Sample Verification** - Manual spot-checks of critical records
3. **Cross-reference Validation** - Verify against source transaction data

### Business Continuity
1. **Phased Implementation** - Create new file alongside existing (don't replace immediately)
2. **Parallel Validation** - Run both old and new files through validation
3. **Stakeholder Review** - Business review before production deployment

---

## ✅ SUCCESS CRITERIA

### Technical Validation
- [ ] **Zero Data Loss** - All 1,537 companies preserved
- [ ] **Sequence Accuracy** - IG_ID to ig_role mapping 100% correct
- [ ] **Transaction Linkage** - All IG_IDs link to valid transactions
- [ ] **Metadata Preservation** - All 25 company fields maintained
- [ ] **Expansion Accuracy** - Multi-transaction companies properly expanded

### Business Validation
- [ ] **Role Accuracy** - Each company's role in each transaction correct
- [ ] **Traceability** - Can trace from company back to source transaction
- [ ] **Import Readiness** - File meets Arcadia import requirements
- [ ] **No Duplicates** - No unnecessary duplicate company creation
- [ ] **Status Integrity** - Company statuses reflect actual state

### Quality Metrics
- **Target Accuracy:** 100% IG_ID-role sequence preservation
- **Coverage Goal:** 100% of transactions linked to companies
- **Error Tolerance:** 0 mapping errors acceptable
- **Data Completeness:** All original metadata preserved

---

## 📈 EXPECTED OUTCOMES

### File Improvements
| Metric | Before | After | Improvement |
|--------|--------|--------|-------------|
| **Columns** | 4 | 25 | +525% metadata |
| **Traceability** | 0% | 100% | Complete linkage |
| **Data Integrity** | Broken | Perfect | Critical fix |
| **Business Intelligence** | Impossible | Full | Complete restoration |

### Business Benefits
1. **Accurate Reporting** - Companies correctly linked to transactions
2. **Investment Analysis** - Proper investor participation tracking
3. **Data Integrity** - Reliable data for business decisions
4. **Import Success** - Clean data for Arcadia database integration

---

## 🚀 IMMEDIATE NEXT STEPS

1. **Approve Plan** - Review and approve this comprehensive fix plan
2. **Execute Backup** - Create secure backup of all current files
3. **Run Analysis** - Compare IMPORT_READY vs standard company file
4. **Implement Fix** - Execute the mapping correction script
5. **Validate Results** - Run all quality assurance tests
6. **Deploy Solution** - Replace broken file with corrected version

---

## ⚠️ CRITICAL REMINDERS

**DO NOT:**
- ❌ Use `companies_import_FINAL_ALL.csv` for ANY production operations
- ❌ Make assumptions about IG_ID-role sequence relationships
- ❌ Lose or modify the source `arcadia_company_unmapped.csv` file

**ALWAYS:**
- ✅ Preserve IG_ID to ig_role positional correspondence
- ✅ Maintain complete company metadata in import files
- ✅ Validate transaction linkages before finalizing
- ✅ Test sequence integrity on every data transformation

---

**This is a CRITICAL data integrity issue that must be resolved before any production operations can proceed safely.**