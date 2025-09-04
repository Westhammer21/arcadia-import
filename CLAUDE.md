# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Transaction Duplicate Detection & Mapping System that maps InvestGame (IG) transactions to Arcadia database records. The system has achieved 98.7% Arcadia coverage with 3,306 of 3,349 transactions successfully mapped.

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

### Unmapped Transaction Processing
```bash
# Map Corporate transactions using context-aware rules
py scripts/map_corporate_unmapped.py

# Enrich unmapped with company data
py scripts/enrich_with_company_data.py

# Standardize investor placeholders
py scripts/process_investor_placeholders.py

# Fix encoding issues in text fields
py scripts/fix_all_encoding_final.py
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
- `ig_arc_unmapped_vF.csv` - 883 unmapped but fully processed transactions

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

### Critical Files - DO NOT DELETE
- `output/ig_arc_mapping_full_vF.csv` - Master mapping
- `output/ig_arc_unmapped_vF.csv` - Enhanced unmapped
- All files in `src/` directory - source data

## Auto-Approval Configuration

This project has auto-approval enabled for all Claude Code operations within the project directory (`C:\Users\sergei\Documents\VS-Code\transactions-check`). Configuration is stored in `.claude/claude_config.json`.