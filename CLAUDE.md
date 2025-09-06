# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Transaction Duplicate Detection & Mapping System that maps InvestGame (IG) transactions to Arcadia database records. The system has achieved 98.7% Arcadia coverage with 3,306 of 3,349 transactions successfully mapped.

**CURRENT STATUS (06-09-2025):** Company Cards phase completed with 260 TO BE CREATED companies validated and backed up. Next phase: Transaction import preparation using ig_arc_unmapped_vF.csv.

## Commands

### Primary Verification & Analysis
```bash
# Verify current mapping status and data integrity
py scripts/verify_arcadia_mapping_complete.py

# List all unmapped Arcadia transactions with details
py scripts/list_unmapped_transactions.py

# Analyze mapping coverage by year
py scripts/analyze_arcadia_coverage.py

# Run 9-point comprehensive verification
py scripts/double_check.py

# Random sample validation
py scripts/random_verification.py
```

### Data Processing
```bash
# Update mappings with new Arcadia export
py scripts/analyze_and_update_mappings.py

# Create enriched mapping with ARC_* columns
py scripts/create_full_mapping.py

# Clean pre-2020 transactions from unmapped
py scripts/clean_pre2020_transactions.py
```

### Transaction Import Preparation (Next Phase)
```bash
# Prepare all unmapped transactions for Arcadia import
py scripts/prepare_all_transactions_import.py

# Prepare transaction import with fixed approach
py scripts/prepare_transaction_import_fixed.py

# Prepare test batch for validation
py scripts/prepare_transaction_import_test.py

# Validate import readiness
py scripts/validate_arcadia_import.py
```

## Architecture & Data Flow

### Core Data Structure
The system operates on three primary datasets:
1. **InvestGame Database** (`src/investgame_database_clean.csv`) - 4,189 transactions
2. **Arcadia Database** (`src/arcadia_database_2025-09-03.csv`) - 3,349 transactions  
3. **Company Profiles** (`src/company-names-arcadia.csv`) - 7,298 companies

### Mapping Logic & Type Conversions

The mapping system uses context-aware rules for transaction types:

**Corporate Transactions** (context-based mapping):
- Size ≤ $5M → `seed` (Early-stage investment)
- Size $5.01-10M → `series a` (Early-stage investment)
- Size > $10M → `undisclosed late-stage` (Late-stage investment)
- Unknown size + Age ≤ 3 years → `undisclosed early-stage`
- Unknown size + Age > 3 years → `undisclosed late-stage`

**Series Mappings**:
- Series A+ → `undisclosed early-stage`
- Series B+ → `undisclosed late-stage`
- Series G, H → `undisclosed late-stage`

All categories are standardized to Arcadia format (singular "investment").

### Output Files

**Primary outputs** in `output/`:
- `ig_arc_mapping_full_vF.csv` - 3,306 mapped transactions with full Arcadia enrichment
- `ig_arc_unmapped_vF.csv` - 883 unmapped but fully processed transactions (NEXT PHASE TARGET)
- `arcadia_company_unmapped.csv` - 1,537 deduplicated company cards (COMPANY CARDS PHASE COMPLETE)
  - 260 TO BE CREATED companies (backed up and ready for Arcadia import)
  - 1,277 existing companies for transaction mapping

**Company Cards Backup** in `archive/company_cards_final_backup_20250906/`:
- `arcadia_company_unmapped_FINAL_20250906.csv` - Final company cards backup
- `ARCADIA_IMPORT_READINESS_REPORT_FINAL_20250906.md` - Final import readiness analysis

Both files are production-ready with:
- 100% Arcadia-compliant types and categories
- Full encoding fixes (ASCII-compliant)
- Standardized country names and sectors
- Company data enrichment where available

### Processing Pipeline

For unmapped transactions, the system applies:
1. Type/category standardization to Arcadia format
2. Encoding fixes for all text fields
3. Company data matching and enrichment (86.4% success rate)
4. Investor placeholder standardization to "Undisclosed" 
5. Country code conversion (US→United States, etc.)
6. Sector corrections (Platform&Tech→Platform & Tech)
7. Marking transactions ready for import (arc_id="TO BE CREATED")

## Key Considerations

### Data Integrity Rules
- Each Arcadia ID maps to exactly one IG record (no duplicates)
- All unmapped Arcadia transactions are verified as legitimate (pre-2020 or DISABLED)
- ARCADIA_TR_ID must match ARC_ID in all enriched records

### File Conventions
- Source data in `src/` is read-only - never modify these files
- All outputs go to `output/` directory
- Historical versions archived in `output/archive/`
- Scripts use UTF-8 encoding for all file operations
- CSV files maintain consistent column ordering

### Import Status (September 2025)
**READY FOR PRODUCTION**: All 260 TO BE CREATED companies validated for Arcadia import
- Strategic/CVC companies: 109 records (41.9%) - Superior data quality
- TestType companies: 151 records (58.1%) - Appropriate placeholders pending classification
- Transaction coverage: 100% via IG_ID linkage integrity
- Quarterly distribution: 74.2% of companies from 2025 transactions (recent expansion)

### Critical Files - DO NOT DELETE
- `output/ig_arc_mapping_full_vF.csv` - Master mapping
- `output/ig_arc_unmapped_vF.csv` - Enhanced unmapped
- `output/arcadia_company_unmapped.csv` - Consolidated company cards ready for Arcadia import
- `ARCADIA_IMPORT_READINESS_REPORT.md` - Comprehensive import analysis
- All files in `src/` directory - source data

### Archived Files
Intermediate company cards files are archived in `output/_archive/company_cards_20250109/`:
- Previous deduplication iterations
- Investor parsing intermediate files
- Comparison and validation outputs

## Auto-Approval Configuration

This project has auto-approval enabled for all Claude Code operations within the project directory (`C:\Users\sergei\Documents\VS-Code\transactions-check`). Configuration is stored in `.claude/claude_config.json`.