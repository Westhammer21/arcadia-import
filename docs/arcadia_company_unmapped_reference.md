# Arcadia Company Unmapped - Reference Documentation
**File**: `output/arcadia_company_unmapped.csv`  
**Created**: 2025-01-09  
**Records**: 1,568 unique companies  
**Purpose**: Consolidated company cards from unmapped transactions ready for Arcadia import

---

## Overview

This file contains deduplicated and merged company cards generated from the 883 unmapped InvestGame transactions. It represents all unique companies (both targets and investors) that need to be created or enriched in the Arcadia database.

## File Structure

### Columns (25 total)

| # | Column | Description | Example Values |
|---|--------|-------------|----------------|
| 1 | **id** | Arcadia ID (empty for new companies) | Empty (except Undisclosed=366) |
| 2 | **status** | Import status | TO BE CREATED, IMPORTED, ENABLED |
| 3 | **name** | Company name | Animoca Brands, Tencent |
| 4 | **also_known_as** | Alternative names | Various |
| 5 | **aliases** | Company aliases | Various |
| 6 | **type** | Company type | Investor, Strategic / CVC |
| 7 | **founded** | Year founded | 2020, 2015, etc. |
| 8 | **hq_country** | Headquarters country | United States, China, etc. |
| 9 | **hq_region** | Headquarters region | North America, Asia, etc. |
| 10 | **ownership** | Ownership type | Private, Public |
| 11 | **sector** | Business sector | Gaming, Technology, etc. |
| 12 | **segment** | Business segment | PC/Console, Mobile, etc. |
| 13 | **features** | Company features | Various |
| 14 | **specialization** | Investment focus | Generalist, Gaming, etc. |
| 15 | **aum** | Assets under management | Numeric or empty |
| 16 | **parent_company** | Parent company name | Various or empty |
| 17 | **transactions_count** | Number of transactions | 0 (for new companies) |
| 18 | **was_added** | Creation timestamp | 05/09/2025 01:23 |
| 19 | **created_by** | Creator (empty) | Empty |
| 20 | **was_changed** | Last modified timestamp | 05/09/2025 01:23 |
| 21 | **modified_by** | Modifier (empty) | Empty |
| 22 | **search_index** | Search keywords | Generated from name, country |
| 23 | **arc_website** | Company website | URLs or empty |
| 24 | **IG_ID** | InvestGame transaction IDs | "123, 456, 789" format |
| 25 | **ig_role** | Roles in transactions | "target, lead, participant" |

## Key Statistics

### Company Distribution
- **Total Unique Companies**: 1,568
- **Companies with Multiple Transactions**: 213
- **Maximum Transactions per Company**: 492 (Undisclosed)

### Role Distribution  
- **Pure Targets**: ~750 companies
- **Pure Investors**: ~795 companies
- **Dual Role (Target & Investor)**: 23 companies

### Notable Dual-Role Companies
Companies that appear as both targets and investors (in different transactions):
- Animoca Brands (6 target, 10 investor transactions)
- Atari (3 target, 3 investor transactions)
- Keywords Studios (2 target, 1 investor transaction)
- And 20 others...

## Data Consolidation Process

This file was created through:
1. **Investor String Parsing**: Complex "Investors / Buyers" strings parsed into individual entities
2. **Deduplication**: Exact name matching to consolidate duplicate entries
3. **Smart Merging**: 97.5% similarity threshold (though all merges were exact matches)
4. **IG_ID Concatenation**: All transaction IDs preserved with ", " separator
5. **Role Preservation**: Roles maintained in order corresponding to IG_IDs
6. **Status Transformation**: "TO BE ENRICHED" → "TO BE CREATED", roles lowercased

## Usage Guidelines

### For Arcadia Import
1. All records with empty `id` field will receive new Arcadia IDs upon import
2. "Undisclosed" retains existing ID=366
3. Status field indicates import readiness
4. All fields are Arcadia-compliant

### IG_ID and Role Correspondence
- The `IG_ID` field contains comma-separated transaction IDs
- The `ig_role` field contains corresponding roles in the same order
- Example: IG_ID "100, 200, 300" with ig_role "target, lead, participant" means:
  - Transaction 100: company was target
  - Transaction 200: company was lead investor
  - Transaction 300: company was participant investor

### Data Integrity
- No company appears as both target and investor in the SAME transaction
- All dual-role companies participate in DIFFERENT transactions
- Data has been validated for import compatibility

## Related Documentation
- **Original Plan**: `docs/company_cards_mapping_plan_FINAL.md`
- **Merge Report**: `docs/company_cards_merge_report.md`
- **Merged Companies Review**: `docs/merged_companies_detailed_review.md`

## Archived Files
Previous iterations and intermediate files archived in:
`output/_archive/company_cards_20250109/`

---

**Note**: This is the definitive company cards file for all unmapped transactions. Use this for any future Arcadia import or enrichment processes.