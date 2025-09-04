# Arcadia Database Export Documentation
**File**: `src/arcadia_database_2025-09-03.csv`  
**Updated**: 03-09-2025  
**Records**: 3,349 gaming investment transactions  
**System**: Exported from Arcadia transaction tracking platform
**Format**: UTF-8 encoded, comma-delimited CSV, 22 columns
**Critical**: 98.7% (3,306 of 3,349) mapped to InvestGame database
**Unmapped**: 43 transactions (36 pre-2020, 7 DISABLED status)

---

## 📊 Database Overview

**KEY DISTINCTION FROM INVESTGAME**: 
- Arcadia: TWO investor columns (Lead Investor / Other Investors)
- InvestGame: ONE investor column (Investors / Buyers with mixed roles)
**PARSING CHALLENGE**: Both databases use commas within investor fields

### Key Statistics (Latest Export: 03-09-2025)
- **Total Transactions**: 3,349
- **Date Range**: 2000-04-29 to 2025-08-31
- **Mapped to InvestGame**: 3,306 (98.7%)
- **Unmapped (Pre-2020)**: 36 transactions
- **Unmapped (DISABLED)**: 7 transactions
- **Status Distribution**:
  - ON APPROVAL: 3,342 (99.8%)
  - DISABLED: 7 (0.2%)

---

## 🔤 Column Structure (30 columns)

### Core Transaction Fields

| Column | Type | Description | Special Notes |
|--------|------|-------------|---------------|
| **ID** | Integer | Unique transaction identifier | Primary key from Arcadia system |
| **Status*** | String | Transaction approval status | Values: IMPORTED (3,060), ON APPROVAL (554), IS INCOMPLETE (24), APPROVED (2), TO DELETE (2), DISABLED (1) |
| **Announcement date*** | Date | Transaction announcement date | Format: YYYY-MM-DD, Required field |
| **Target Company** | String | Company being invested in/acquired | Links to Company model in Arcadia |
| **Transaction Size*, $M** | Decimal | Investment amount in millions USD | **0.0 = UNDISCLOSED** (1,219 records, 33.5%) |
| **Transaction Type*** | String | Type of transaction | See Transaction Types section |
| **Transaction Category*** | String | High-level transaction category | Early-stage, Late-stage, M&A, or Public offering |
| **closed date** | Date | Transaction closing date | May be empty if not closed |
| **To be closed** | Boolean | Whether transaction is pending | 0 = closed, 1 = pending |

### 🔑 Investor Columns (CRITICAL FOR PARSING)

| Column | Type | Records with Data | Multiple Investors |
|--------|------|------------------|--------------------|
| **Lead Investor / Acquirer** | String | 3,311 (90.9%) | 556 records (16.8% of those with leads) have comma-separated multiple leads |
| **Other Investors** | String | 1,203 (33.0%) | 1,058 records (88% of those with others) have comma-separated multiple investors |

#### Investor Parsing Examples
```
Lead Investor Examples:
- Single: "The Raine Group"
- Multiple: "Menlo Ventures, Transcend Fund"
- Multiple (3+): "Animoca Brands, Galaxy Interactive, Kleiner Perkins"

Other Investors Examples:
- Simple list: "Makers Fund, MIT, QIA, Shamrock Capital"
- With individuals: "1Up Ventures, Chris Rigopulos, CohhCarnage, Nate Mitchell"
- Mixed entities: "Andreessen Horowitz, BITKRAFT Ventures, F4 Fund, Siqi Chen Access Fund"
```

### Transaction Details

| Column | Type | Description | Business Logic |
|--------|------|-------------|----------------|
| **Source URL*** | URL | Official source of information | Required, validates URL format |
| **Description*** | Text | Rich text transaction description | 10-150 word requirement in Arcadia |
| **Transaction UUID** | UUID | Unique identifier | Auto-generated, used for API operations |

### Financial Details (M&A specific)

| Column | Type | Description | Usage |
|--------|------|-------------|-------|
| **Equity Value at Listing, $M** | Decimal | IPO/SPAC listing value | Only for public offerings |
| **M&A Details: Equity Value** | Decimal | Company equity value | M&A transactions only |
| **M&A Details: Upfront Enterprise Value** | Decimal | Initial purchase price | M&A transactions |
| **M&A Details: Upfront Stake Acquired, %** | Decimal | Ownership percentage | M&A minority stakes |
| **M&A Details: Maximum Enterprise Value, $M** | Decimal | Maximum deal value with earnouts | M&A with earnouts |
| **M&A Details: Maximum Earn Out, $M** | Decimal | Maximum earnout amount | Performance-based payments |

### System & Tracking Fields

| Column | Type | Description | Purpose |
|--------|------|-------------|---------|
| **signature company** | String | Processed target name | Duplicate detection |
| **signature date** | String | Date in YYmonth format | Duplicate detection |
| **signature investor** | String | Concatenated lead investors | Duplicate detection |
| **signature deal type** | String | Normalized transaction type | Duplicate detection |
| **source data** | String | Combined investor data | System tracking |
| **created at** | DateTime | Record creation timestamp | Audit trail |
| **Internal information** | Text | Internal notes | Not for external use |

---

## 📈 Transaction Types Distribution

| Type | Count | Category | Lead Investor Requirement |
|------|-------|----------|---------------------------|
| **Seed** | 1,386 | Early-stage | Optional |
| **M&A control (incl. LBO/MBO)** | 1,049 | M&A | 1-3 required |
| **Series A** | 435 | Early-stage | Optional |
| **Undisclosed Early-stage** | 185 | Early-stage | Optional |
| **Undisclosed Late-stage** | 127 | Late-stage | Optional |
| **M&A minority** | 109 | M&A | 1-3 required |
| **Series B** | 103 | Late-stage | Optional |
| **Accelerator / Grant** | 65 | Early-stage | Not required |
| **PIPE** | 62 | Public offering | Optional |
| **Fixed Income** | 31 | Late-stage | Optional |

---

## 🔍 Data Quality Indicators

### Status Distribution
- **IMPORTED**: 3,060 records (84.0%) - Imported from external sources
- **ON APPROVAL**: 554 records (15.2%) - Pending approval
- **IS INCOMPLETE**: 24 records (0.7%) - Missing required data
- **APPROVED**: 2 records - Fully approved
- **TO DELETE**: 2 records - Marked for deletion
- **DISABLED**: 1 record - Hidden from system

### Investment Disclosure
- **Disclosed amounts**: 2,424 transactions ($316.5B total)
- **Undisclosed (0.0)**: 1,219 transactions
- **Average disclosed deal**: $130.5M
- **Median disclosed deal**: $15.0M (estimated)

### Investor Participation
- **Lead investor present**: 90.9% of transactions
- **Multiple lead investors**: 556 records (16.8% of those with leads)
- **Other investors present**: 33.0% of transactions
- **Solo investor deals**: ~57% (lead only, no others)

---

## 💡 Usage Guidelines

### Parsing Investor Columns

```python
import pandas as pd

def parse_investors(investor_string):
    """Parse comma-separated investor string"""
    if pd.isna(investor_string):
        return []
    
    # Split by comma and clean
    investors = [inv.strip() for inv in investor_string.split(',')]
    return [inv for inv in investors if inv]

# Example usage
df = pd.read_csv('arcadia_database.csv')

# Parse lead investors
df['lead_investor_list'] = df['Lead Investor / Acquirer'].apply(parse_investors)

# Parse other investors
df['other_investor_list'] = df['Other Investors'].apply(parse_investors)

# Count investors per transaction
df['total_lead_count'] = df['lead_investor_list'].apply(len)
df['total_other_count'] = df['other_investor_list'].apply(len)
```

### Handling Undisclosed Values

```python
# Mark undisclosed transactions
df['amount_disclosed'] = df['Transaction Size*, $M'] > 0

# Calculate statistics on disclosed amounts only
disclosed_df = df[df['amount_disclosed']]
total_disclosed = disclosed_df['Transaction Size*, $M'].sum()
```

### Transaction Category Mapping

Based on Arcadia system documentation:
- **Early-stage**: Seed, Series A, Accelerator/Grant, Undisclosed Early-stage
- **Late-stage**: Series B+, Growth/Expansion, PIPE, Fixed Income
- **M&A**: M&A control, M&A minority (requires lead investors)
- **Public offering**: IPO, SPAC, Listing

---

## ⚠️ Important Considerations

### 🔴 Critical Session Recovery Notes
1. **CSV Reading**: pandas.read_csv() handles quoted commas automatically
2. **Investor Parsing**: Split by comma AFTER DataFrame load, not during
3. **M&A Validation**: 1,158 M&A transactions require 1-3 lead investors
4. **Status Priority**: IMPORTED (84%) needs review, ON APPROVAL (15.2%) pending
5. **Undisclosed**: 0.0 means undisclosed (never zero investment)

### Data Integrity Rules (from Arcadia system)
1. **Lead Investor Requirements**: M&A transactions MUST have 1-3 lead investors
2. **Status Constraints**: Companies in approved transactions cannot be deleted
3. **Date Validation**: Closed date must be ≥ announcement date
4. **Duplicate Detection**: System uses signature fields to identify potential duplicates (70% similarity threshold)

### Unicode & Encoding
- Database supports full Unicode for international company/investor names
- Ensure UTF-8 encoding when processing
- Special characters in descriptions may include smart quotes, em-dashes

### Relationship Mapping
- Target Company links to Arcadia Company model
- Lead/Other Investors link to Company model as ManyToMany relationships
- Parent company relationships updated for M&A control transactions

---

## 📝 SQL Query Examples

```sql
-- Find all Animoca Brands investments
SELECT * FROM arcadia_database 
WHERE "Lead Investor / Acquirer" LIKE '%Animoca Brands%'
   OR "Other Investors" LIKE '%Animoca Brands%';

-- Get M&A transactions over $100M
SELECT "Target Company", "Transaction Size*, $M", "Lead Investor / Acquirer"
FROM arcadia_database
WHERE "Transaction Type*" LIKE 'M&A%'
  AND "Transaction Size*, $M" > 100;

-- Monthly investment trends
SELECT DATE_FORMAT("Announcement date*", '%Y-%m') as month,
       COUNT(*) as deals,
       SUM("Transaction Size*, $M") as total_investment
FROM arcadia_database
WHERE "Transaction Size*, $M" > 0
GROUP BY month
ORDER BY month DESC;
```

---

## 🔄 Sync with Arcadia System

This CSV export represents a snapshot of the Arcadia system. For production use:
1. Transactions with status "IMPORTED" need review and approval
2. "IS INCOMPLETE" records require data completion
3. "ON APPROVAL" transactions are in the approval workflow
4. Regular re-exports needed to capture system updates

---

## 🎯 Quick Session Recovery

```python
import pandas as pd

# Load database (standard CSV, UTF-8)
df = pd.read_csv('arcadia_database.csv')

# Parse investor columns (AFTER loading)
df['lead_list'] = df['Lead Investor / Acquirer'].str.split(',').apply(
    lambda x: [i.strip() for i in x] if isinstance(x, list) else []
)
df['other_list'] = df['Other Investors'].str.split(',').apply(
    lambda x: [i.strip() for i in x] if isinstance(x, list) else []
)

# Key validation
print(f"Records: {len(df)}")
print(f"With leads: {df['Lead Investor / Acquirer'].notna().sum()}")
print(f"Disclosed: {(df['Transaction Size*, $M'] > 0).sum()}")
print(f"Date range: {df['Announcement date*'].min()} to {df['Announcement date*'].max()}")
```
**END OF DOCUMENTATION**