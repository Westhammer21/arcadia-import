# Scripts Documentation - Transaction Mapping System
**Updated**: 03-09-2025 (Post-Cleanup)  
**Active Scripts**: 10 essential Python scripts
**Archived Scripts**: 18 historical scripts in `_archive/`
**Purpose**: Streamlined toolkit for IG-Arcadia database mapping and verification

---

## ✅ ACTIVE SCRIPTS (10 Essential Tools)

### 🎯 Primary Verification & Mapping Scripts

| Script | Purpose | Usage | Output |
|--------|---------|-------|--------|
| **`verify_arcadia_mapping_complete.py`** | Comprehensive mapping verification | `py scripts/verify_arcadia_mapping_complete.py` | Full verification report |
| **`list_unmapped_transactions.py`** | Lists all 43 unmapped Arcadia deals | `py scripts/list_unmapped_transactions.py` | Detailed unmapped list |
| **`analyze_and_update_mappings.py`** | Updates mappings with latest Arcadia data | `py scripts/analyze_and_update_mappings.py` | Updated mapping file |

### 📊 Analysis & Coverage Scripts

| Script | Purpose | Key Features |
|--------|---------|--------------|
| **`analyze_arcadia_coverage.py`** | Analyzes mapping coverage by year | Coverage statistics, gap analysis |
| **`double_check.py`** | 9-point verification system | Comprehensive validation checks |
| **`random_verification.py`** | Random sample validation | Statistical confidence testing |
| **`verify_mapping_data.py`** | Validates data integrity | Column checks, ID verification |

### 🧹 Data Cleanup Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| **`clean_pre2020_transactions.py`** | Removes pre-2020 from unmapped | Before final analysis |
| **`remove_pre_2020.py`** | Filters pre-2020 transactions | Data preparation |

### 🔧 Core Processing Script

| Script | Purpose | Dependencies |
|--------|---------|--------------|
| **`create_full_mapping.py`** | Creates enriched mapping with ARC_* columns | Requires base mapping |

---

## 📂 Archived Scripts (Historical Reference)

Located in `scripts/_archive/` - 18 completed scripts including:
- Initial mapping creation scripts
- Duplicate detection algorithms  
- Manual correction processors
- One-time analysis tools

These scripts completed their purpose and are retained for historical reference only.

---

## 🎯 Common Workflows

### 1. Verify Current Mapping Status
```bash
# Check comprehensive mapping status
py scripts/verify_arcadia_mapping_complete.py

# List unmapped transactions with details
py scripts/list_unmapped_transactions.py
```

### 2. Update with New Arcadia Export
```bash
# When new Arcadia export is available
# 1. Place new export in src/ folder
# 2. Run update script
py scripts/analyze_and_update_mappings.py

# 3. Verify the updates
py scripts/verify_arcadia_mapping_complete.py
```

### 3. Data Quality Checks
```bash
# Random sampling validation
py scripts/random_verification.py

# Coverage analysis by year
py scripts/analyze_arcadia_coverage.py

# 9-point verification
py scripts/double_check.py
```

### 4. Data Cleanup (When Needed)
```bash
# Remove pre-2020 transactions from analysis
py scripts/clean_pre2020_transactions.py

# Or use the filter script
py scripts/remove_pre_2020.py
```

---

## 📋 Script Details

### verify_arcadia_mapping_complete.py
- **Purpose**: Main verification tool for IG-Arcadia mapping
- **Checks**: Coverage percentage, duplicate IDs, unmapped analysis
- **Output**: Console report + JSON summary
- **Key Metrics**: 98.7% coverage confirmed

### list_unmapped_transactions.py  
- **Purpose**: Displays all unmapped Arcadia transactions
- **Output**: Formatted table with ID, Status, Dates, Company
- **Finding**: 43 unmapped (36 pre-2020, 7 DISABLED)

### analyze_and_update_mappings.py
- **Purpose**: Updates existing mapping with new Arcadia data
- **Process**: Matches IDs, updates ARC_* columns
- **Recent**: Applied 27 ARCADIA_TR_ID corrections

### analyze_arcadia_coverage.py
- **Purpose**: Detailed coverage analysis by year
- **Output**: Year-by-year mapping statistics
- **Finding**: Coverage ranges from 53.6% (2025) to 84.9% (2022)

### create_full_mapping.py
- **Purpose**: Enriches base mapping with Arcadia columns
- **Adds**: 15 ARC_* prefixed columns
- **Result**: Complete data enrichment

---

## 📦 Dependencies

### Required Python Packages:
```python
pandas >= 1.3.0
numpy >= 1.21.0
pathlib (standard library)
json (standard library)
datetime (standard library)
```

### Required Files:
```
src/
├── investgame_database_clean.csv    # Base IG data (4,189 records)
├── arcadia_database_2025-09-03.csv  # Latest Arcadia (3,349 records)
└── company-names-arcadia.csv        # Company profiles (7,298)

output/
└── ig_arc_mapping_full_vF.csv       # Master mapping file
```

---

## ⚠️ Important Notes

1. **Always work with copies** - Never modify source files directly
2. **Check dates on Arcadia exports** - Database updates frequently  
3. **Verify after updates** - Run verification script after any changes
4. **Pre-2020 transactions** - InvestGame doesn't track these (expected unmapped)
5. **DISABLED status** - Cancelled deals (expected unmapped)

---

## 🔄 Maintenance Schedule

### Weekly Tasks:
- Run `verify_arcadia_mapping_complete.py` to check status

### When New Arcadia Export Available:
1. Download new export to `src/` with date suffix
2. Run `analyze_and_update_mappings.py`
3. Verify with `verify_arcadia_mapping_complete.py`
4. Document any changes in README

### Monthly Review:
- Check coverage trends with `analyze_arcadia_coverage.py`
- Review unmapped with `list_unmapped_transactions.py`

---

## 📈 Current System Metrics (03-09-2025)

- **Total IG Records**: 4,189
- **Total Arcadia Records**: 3,349  
- **Mapped Successfully**: 3,306 (98.7%)
- **Legitimate Unmapped**: 43 (1.3%)
- **Duplicate ID Issues**: 0 (Perfect integrity)
- **Scripts Maintained**: 10 active + 18 archived

---

**Maintained by**: AI Analytics Team | **Version**: 2.0 (Post-Cleanup)