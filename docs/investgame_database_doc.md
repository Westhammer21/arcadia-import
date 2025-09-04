# InvestGame Database Documentation
**Updated**: 03-09-2025  
**Status**: ✅ FULLY MAPPED TO ARCADIA
**Purpose**: Gaming industry investment tracking (2020-2025)
**Critical**: Source of truth for gaming investments, now 78.9% mapped to Arcadia

---

## 📁 **File Locations & Formats**

### Current Master Files:
- **Mapped Database**: `output/ig_arc_mapping_full_vF.csv`
  - Format: UTF-8, comma-delimited CSV
  - Rows: 4,189 | Columns: 39 (21 IG + 2 mapping + 15 ARC + 1 human review)
  - **3,306 records mapped to Arcadia (78.9%)**
  
### Source Files:
- **Cleaned Database**: `src/investgame_database_clean.csv`
  - Format: UTF-8, comma-delimited CSV
  - Rows: 4,189 | Columns: 20
  - Base InvestGame data (2020-2025)

---

## 📊 **Database Overview**

### Statistics:
- **Total Records**: 4,189 gaming investment transactions
- **Date Range**: 2020-01-01 to 2025-08-27
- **Total Disclosed Investment**: $311.9 billion
- **Average Deal Size**: $107.27m (disclosed only)
- **Columns**: 20 (19 original + 1 new `Amount_Status`)

### Investment Distribution:
| Type | Count | Percentage |
|------|-------|------------|
| Seed round | 1,587 | 37.9% |
| Control (M&A) | 1,048 | 25.0% |
| Series A | 464 | 11.1% |
| Corporate | 302 | 7.2% |

### Sector Breakdown:
- **Gaming**: 1,970 (47.0%)
- **Platform&Tech**: 1,650 (39.4%)
- **Esports**: 350 (8.4%)

---

## 🔧 **Column Structure**

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **Date** | Date | Transaction date (DD/MM/YYYY) | |
| **Year** | Integer | Year of transaction | |
| **Quarter** | String | Fiscal quarter (Q[1-4]'YY) | |
| **Target name** | String | Company receiving investment | |
| **Investors / Buyers** | String | ALL investors in ONE column | Mixed separators: commas, slashes, parentheses for roles (Lead) |
| **Type** | String | Investment type | Seed, Series A/B, Control, etc. |
| **Category** | String | Investment category | Early/Late-stage VC, M&A, Corporate |
| **AI** | String | AI-related flag | Yes/No |
| **Size, $m** | Float | Investment amount (millions USD) | **0.00 = UNDISCLOSED** |
| **% acquired** | Float | Ownership percentage | Numeric (% removed) |
| **Sector** | String | Industry sector | Gaming/Platform&Tech/Esports |
| **Segment** | String | Market subsegment | Mobile/PC&Console/Blockchain etc. |
| **Target's Country** | String | Target company location | |
| **Region** | String | Geographic region | |
| **Target Founded** | Integer | Year company founded | |
| **Gender** | String | Founder gender | Often null |
| **Target's Website** | URL | Company website | |
| **Short Deal Description** | Text | Deal summary | |
| **Deal Link** | URL | Source article | |
| **Amount_Status** | String | **NEW COLUMN** | DISCLOSED/UNDISCLOSED/NULL |

---

## 🔑 **Critical Parsing Information**

### Investor Column Format:
- **Single column** contains ALL investors (unlike Arcadia's two columns)
- **Separators**: Primarily commas, but also "/", "&", ";"
- **Role indicators**: "(Lead)", "(Co-lead)" embedded in text
- **Example**: "Sequoia Capital (Lead), a16z, Tencent / Sony Ventures"

## 💻 **How to Use**

### Reading the Database:
```python
import pandas as pd

# Read cleaned database
df = pd.read_csv('tables/transactions-check/investgame_database_clean.csv', 
                 encoding='utf-8')

# Key operations
# 1. Filter undisclosed deals
undisclosed = df[df['Amount_Status'] == 'UNDISCLOSED']

# 2. Parse multiple investors
investors_list = df['Investors / Buyers'].str.split(',')

# 3. Calculate metrics
total_disclosed = df[df['Amount_Status'] == 'DISCLOSED']['Size, $m'].sum()
```

### Processing Raw File (if needed):
```python
# For raw TAB-delimited file
df_raw = pd.read_csv('investgame-database.csv', 
                     sep='\t',
                     encoding='windows-1252',  # Best encoding for this file
                     dtype=str,
                     keep_default_na=False)
```

---

## 🛠️ **Processing Applied**

### Encoding Fixes (1,542 issues resolved):
- Windows-1252 encoding used for proper reading
- Character conversions applied:
  - `�` → `'` (apostrophe)
  - `£` → `GBP`
  - Accented letters → ASCII (é→e, ö→o, ü→u)
  - Smart quotes → Regular quotes

### Data Standardization:
- **Nulls**: "null" and "-" → NaN
- **Percentages**: Removed % sign, converted to numeric
- **Amounts**: 0.00 marked as UNDISCLOSED (1,281 records)
- **Tickers**: Preserved in parentheses (e.g., NYSE: RBLX)

---

## ⚠️ **Critical Session Recovery Info**

1. **Undisclosed Amounts**: `Size, $m = 0.00` ALWAYS means undisclosed (1,281 records)
2. **Investor Parsing**: Single column with mixed separators - parse AFTER CSV reading
3. **Encoding**: MUST use Windows-1252 for raw file, UTF-8 for cleaned
4. **Stock Tickers**: Preserved as "(NYSE: MSFT)" format
5. **Amount_Status**: Added column with DISCLOSED/UNDISCLOSED/NULL values
6. **Key difference from Arcadia**: Single investor column vs. Lead/Other split

---

## 📈 **Quick Stats**

- **Disclosed deals**: 2,908 (69.4%)
- **Undisclosed deals**: 1,281 (30.6%)
- **Countries represented**: Multiple (US, UK, Netherlands, Japan, etc.)
- **Time span**: 5.7 years of data

---

**END OF DOCUMENTATION**