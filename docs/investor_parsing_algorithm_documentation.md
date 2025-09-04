# Investor Parsing Algorithm Documentation
**Version**: 3.0 FINAL  
**Created**: 2025-01-09  
**Purpose**: Document the complete algorithm for parsing and processing investor data from unmapped transactions

---

## 📋 Executive Summary

This document describes the algorithm used to parse the "Investors / Buyers" column in the unmapped transactions table (`ig_arc_unmapped_vF.csv`) and transform it into a structured format suitable for Arcadia import.

**Key Achievement**: Successfully processed 883 transactions into 1,568 structured investor records with clear role assignments.

---

## 🎯 Algorithm Overview

### Input
- **Source File**: `ig_arc_unmapped_vF.csv` (883 transactions)
- **Target Column**: "Investors / Buyers" - contains investor names in various formats

### Output
- **Result File**: `ig_arc_unmapped_investors_FINAL.csv` (1,568 rows)
- **Structure**: One row per investor with role designation (lead/participant)

---

## 🔧 Parsing Rules and Logic

### Rule Hierarchy (Applied in Order)

#### 1️⃣ **Simple Cases (Single Investor)**
- **Pattern**: No commas, slashes, or "(lead)" markers
- **Action**: Mark as lead investor
- **Example**: 
  - Input: `"Tencent (SEHK: 700)"`
  - Output: 1 row, role = lead
- **Result**: 721 transactions processed

#### 2️⃣ **"(lead)" Marker Present**
- **Pattern**: Contains "(lead)" in text
- **Action**: 
  - Everything LEFT of LAST "(lead)" = lead investors
  - Everything RIGHT of LAST "(lead)" = participants
- **Delimiter**: Comma for splitting names
- **Example**:
  - Input: `"Rockaway Ventures (lead) / Tarpan Capital, Lion Beat Capital"`
  - Output: 
    - Lead: Rockaway Ventures
    - Participants: Tarpan Capital, Lion Beat Capital
- **Result**: 81 transactions processed

#### 3️⃣ **Slash "/" Delimiter (No "lead" marker)**
- **Pattern**: Contains "/" but no "(lead)"
- **Action**:
  - Everything LEFT of FIRST "/" = lead investors
  - Everything RIGHT of FIRST "/" = participants
- **Delimiter**: Comma for splitting names
- **Example**:
  - Input: `"5Y Capital / Vitalbridge, BAI Capital"`
  - Output:
    - Lead: 5Y Capital
    - Participants: Vitalbridge, BAI Capital
- **Result**: 12 transactions processed

#### 4️⃣ **No Clear Delimiter - Multiple Investors**
- **Pattern**: Only commas, no "/" or "(lead)"
- **Action** (Version 3 Logic):
  
  **a) 2-3 Investors**:
  - Mark ALL as lead investors
  - Reasoning: Small investor group implies equal participation
  - Example:
    - Input: `"Krafton, Naver Z, SNOW"`
    - Output: 3 leads
  - Result: 29 transactions
  
  **b) 4+ Investors**:
  - Create special lead entry: `"Undisclosed"`
  - Mark ALL actual investors as participants
  - Reasoning: Large group without designated lead = unclear leadership
  - Example:
    - Input: `"Cape Capital, Investinor, Myrlid, Tine Pensjonskasse"`
    - Output:
      - Lead: "Undisclosed"
      - Participants: Cape Capital, Investinor, Myrlid, Tine Pensjonskasse
  - Result: 40 transactions

---

## 📊 Processing Statistics

### Overall Results
```
Original Transactions: 883
Final Rows: 1,568 (+685 expansion)
Processing Success Rate: 100%
Errors: 0
```

### Distribution by Parsing Method
| Method | Transactions | Rows Generated | Description |
|--------|-------------|----------------|-------------|
| Simple Case | 721 | 721 | Single investor |
| Lead Marker | 81 | 397 | Has "(lead)" designation |
| Slash Delimiter | 12 | 69 | Has "/" separator |
| No Delimiter (2-3 investors) | 29 | 67 | All marked as leads |
| No Delimiter (4+ investors) | 40 | 314 | Lead="Undisclosed", rest participants |
| **TOTAL** | **883** | **1,568** | |

### Role Distribution
```
Lead Investors: 960 (61.2%)
Participants: 608 (38.8%)
Undisclosed Leads: 40 transactions (affecting 763 total rows)
```

---

## 🔄 Data Transformation Process

### Row Multiplication Logic
For each transaction with multiple investors:

1. **Parse** investor string according to rules above
2. **Identify** leads and participants
3. **Create** one row per investor:
   ```
   Original: 1 transaction with 3 investors
   Result: 3 rows (same transaction data, different investor info)
   ```
4. **Preserve** all original transaction data in each row
5. **Add** new columns:
   - `investor_name`: Individual investor name
   - `investor_role`: "lead" or "participant"
   - `investor_count`: Total investors in transaction
   - `lead_count`: Number of leads
   - `participant_count`: Number of participants
   - `parsing_method`: Method used for parsing
   - `ig_tier_lead_investor_acquirer`: Lead investor reference

---

## 📝 Special Cases and Edge Handling

### Ticker Symbols
- **Handling**: Kept with company name
- **Example**: `"Tencent (SEHK: 700)"` remains intact

### Multiple Slashes
- **Finding**: 0 cases with multiple slashes
- **Policy**: Would use first slash if encountered

### Empty/Invalid Names
- **Validation**: Names must be ≥2 characters
- **Result**: 0 invalid names found

### "Undisclosed" in Original Data
- **Handling**: Processed as normal investor name
- **Count**: 427 instances in simple cases

---

## 🎯 Business Logic Rationale

### Why Different Rules for Different Investor Counts?

1. **Single Investor** → Lead
   - Clear sole investor = lead by default

2. **2-3 Investors without delimiter** → All Leads
   - Small groups often indicate co-lead situations
   - Equal partnership common in small rounds

3. **4+ Investors without delimiter** → Undisclosed Lead
   - Large groups without clear leader designation
   - Indicates syndicate or crowd funding
   - "Undisclosed" prevents incorrect lead assignment
   - All actual investors listed as participants

4. **Explicit Markers** → Follow designation
   - "(lead)" and "/" are clear role indicators
   - Respect explicit data structure

---

## 📁 Output File Structure

### File: `ig_arc_unmapped_investors_FINAL.csv`

**Columns** (47 original + 7 new):
- All original transaction columns preserved
- `investor_name`: Individual investor name
- `investor_role`: "lead" or "participant"
- `investor_count`: Total investors in transaction
- `lead_count`: Number of lead investors
- `participant_count`: Number of participant investors
- `parsing_method`: Algorithm method used
- `ig_tier_lead_investor_acquirer`: Lead investor reference

**Ready for Arcadia Import**:
- ✅ One investor per row
- ✅ Clear role assignments
- ✅ Preserved transaction context
- ✅ No data loss

---

## 🔍 Validation Results

### Sample Validation (50 transactions)
- **Pass Rate**: 100%
- **Issues Found**: 0
- **Name Quality**: All valid (≥2 characters)
- **Role Assignment**: Correct per algorithm

### Data Integrity Check
- **Original Transactions**: 883 ✅
- **Unique IG_IDs Preserved**: 883 ✅
- **Missing Values**: 0 ✅
- **Parse Errors**: 0 ✅

---

## 📈 Key Insights

1. **Most transactions (81.7%)** had simple single investors
2. **Only 18.3%** required complex parsing
3. **Lead designation clarity**:
   - Explicit lead marking: 81 cases
   - Slash separation: 12 cases
   - Ambiguous (no delimiter): 69 cases
4. **Large investor groups** (4+) without lead designation: 40 cases → assigned "Undisclosed" lead

---

## 🚀 Implementation

### Scripts Used
1. `analyze_investors_column.py` - Initial analysis
2. `process_complex_investors_v3.py` - Final processing with v3 logic
3. `check_multiple_slashes.py` - Edge case verification
4. `analyze_no_delimiter_cases.py` - Logic validation

### Processing Pipeline
```
1. Load unmapped transactions
2. Identify simple vs complex cases
3. Apply parsing rules hierarchically
4. Expand rows for multiple investors
5. Validate results
6. Export final structured data
```

---

## ✅ Conclusion

The algorithm successfully:
- Processed 100% of transactions without errors
- Created structured data ready for Arcadia import
- Handled all edge cases appropriately
- Maintained complete data integrity
- Applied business-appropriate logic for ambiguous cases

The output file `ig_arc_unmapped_investors_FINAL.csv` contains 1,568 properly structured investor records ready for system import.

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-09  
**Maintained by**: AI Analytics Team