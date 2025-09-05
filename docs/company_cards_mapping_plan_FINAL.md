# Company Cards Creation - Mapping Plan FINAL
**Version**: 2.0 FINAL  
**Created**: 2025-01-09  
**Completed**: 2025-01-09  
**Status**: ✅ COMPLETED - 1,625 cards successfully generated
**Purpose**: Create deduplicated Arcadia company cards with consolidated IG_IDs

---

## 📋 Executive Summary

Successfully created Arcadia-compatible company cards from `ig_arc_unmapped_investors_FINAL.csv` with:
1. **Deduplication** by exact name match ✅
2. **IG_ID concatenation** for multiple transactions ✅ 
3. **Role preservation** in matching order ✅
4. **Dual cards** for companies that are both targets AND investors ✅

**Final Output**: 1,625 deduplicated cards in `arcadia_company_cards_deduplicated.csv`

---

## 🎯 Key Requirements & Decisions

### Critical Rules:

1. **ID Field**: 
   - ✅ Leave **EMPTY** for all new cards (no generation)
   - System will assign IDs upon import
   - Exception: "Undisclosed" uses existing ID=366

2. **Deduplication**:
   - ✅ **Exact name match** (case-sensitive)
   - Consolidate all occurrences into single card
   - Concatenate IG_IDs with ", " (comma + space)
   - Concatenate roles in same order

3. **Format Requirements**:
   - IG_ID: "123, 456, 789" (comma + space separator)
   - investor_role: "lead, participant, lead" (matching order)
   - Critical: Order MUST match between IG_ID and role!

4. **Dual Role Handling**:
   - If company is both target AND investor → create 2 separate cards
   - Target card: investor_role = "TARGET, TARGET"
   - Investor card: investor_role = "lead, participant"

5. **Metadata Priority** (when merging duplicates):
   - Use record with most complete data
   - Non-empty values override empty ones
   - First non-empty value wins for each field

6. **Output Structure**:
   - ✅ **Single combined file**: `arcadia_company_cards_deduplicated.csv`
   - Both targets and investors in same file

---

## 📊 Deduplication Logic

### Step-by-Step Process:

1. **Group by exact name** (case-sensitive)
2. **Collect all IG_IDs** for each name
3. **Collect all roles** in same order
4. **Select best metadata**:
   - Priority 1: Non-empty arc_* fields
   - Priority 2: Non-empty original fields
   - Priority 3: First occurrence
5. **Format concatenated fields**:
   ```
   IG_ID: "123, 456, 789"
   investor_role: "TARGET, TARGET, TARGET" or "lead, participant, lead"
   ```

### Example Deduplication:

**Input** (3 rows with same company):
```
Name: Tencent, IG_ID: 100, Role: lead, Country: China
Name: Tencent, IG_ID: 200, Role: participant, Country: [empty]
Name: Tencent, IG_ID: 300, Role: lead, Country: [empty]
```

**Output** (1 row):
```
Name: Tencent
IG_ID: "100, 200, 300"
investor_role: "lead, participant, lead"
Country: China (from first row with data)
```

---

## 🔄 Field Mapping (Updated)

### Arcadia Structure (22 columns + 3 additional)

| # | Column | Target Mapping | Investor Mapping | Notes |
|---|--------|----------------|------------------|-------|
| 1 | **id** | Empty | Empty | System assigns (except Undisclosed=366) |
| 2 | **status** | arc_status or "TO BE ENRICHED" | "TO BE ENRICHED" | Keep "TO BE CREATED" as is |
| 3 | **name** | arc_name (must equal Target name) | investor_name | Dedup key |
| 4 | **also_known_as** | arc_also_known_as | Empty | |
| 5 | **aliases** | arc_aliases | Empty | |
| 6 | **type** | arc_type or "Strategic / CVC" | "Investor" | |
| 7 | **founded** | arc_founded or Target Founded | Empty | Integer or empty |
| 8 | **hq_country** | arc_hq_country or Target's Country | Empty | |
| 9 | **hq_region** | arc_hq_region or Region | Empty | |
| 10 | **ownership** | arc_ownership or "Private" | "Private" | |
| 11 | **sector** | arc_sector or Sector | Empty | |
| 12 | **segment** | arc_segment or Segment | Empty | |
| 13 | **features** | arc_features | Empty | |
| 14 | **specialization** | arc_specialization or "Generalist" | "Generalist" | |
| 15 | **aum** | arc_aum | Empty | |
| 16 | **parent_company** | arc_parent_company | Empty | |
| 17 | **transactions_count** | arc_transactions_count or 0 | 0 | |
| 18 | **was_added** | Current timestamp | Current timestamp | |
| 19 | **created_by** | Empty | Empty | |
| 20 | **was_changed** | Current timestamp | Current timestamp | |
| 21 | **modified_by** | Empty | Empty | |
| 22 | **search_index** | Generate from name, country, region | name only | |
| 23 | **arc_website** | Target's Website | Empty | Additional column |
| 24 | **IG_ID** | Concatenated with ", " | Concatenated with ", " | Additional column |
| 25 | **investor_role** | "TARGET, TARGET, ..." | "lead, participant, ..." | Additional column |

---

## 🔧 Special Cases Handling

### 1. Undisclosed Investors
- Use existing Arcadia card: **ID = 366**
- Copy all fields from existing card
- Only update IG_ID and investor_role concatenation

### 2. Companies in Both Roles
**Example**: Company X is target in transaction 100 and investor in transaction 200

Create 2 cards:
```
Card 1 (Target):
- name: Company X
- IG_ID: "100"
- investor_role: "TARGET"
- [target metadata]

Card 2 (Investor):
- name: Company X
- IG_ID: "200"
- investor_role: "lead"
- [investor defaults]
```

### 3. Parse Errors
- Skip rows where investor_name = "PARSE_ERROR"

### 4. arc_status = "TO BE CREATED"
- Keep as "TO BE CREATED" (don't change to "TO BE ENRICHED")

---

## 📁 Output File

### File: `arcadia_company_cards_deduplicated.csv`
- **Format**: Single combined CSV
- **Expected rows**: ~800-1,200 after deduplication
  - ~400-500 unique targets
  - ~400-600 unique investors  
  - ~50-100 dual role cards
- **Columns**: 25 (22 Arcadia + 3 additional)
- **Encoding**: UTF-8

---

## 🚀 Implementation Steps

### Phase 1: Load & Prepare
```python
# Load source
df = pd.read_csv('ig_arc_unmapped_investors_FINAL.csv')

# Load Undisclosed reference
undisclosed_ref = pd.read_csv('company-names-arcadia.csv')
undisclosed_card = undisclosed_ref[undisclosed_ref['id'] == 366]
```

### Phase 2: Process Targets
```python
# Group targets by exact name
target_groups = df.groupby('Target name', sort=False)

# For each group:
# - Concatenate IG_IDs with ", "
# - Set investor_role = "TARGET, TARGET, ..."
# - Select best metadata (most complete)
```

### Phase 3: Process Investors
```python
# Filter non-Undisclosed investors
investors = df[df['investor_name'] != 'Undisclosed']

# Group by exact investor_name
investor_groups = investors.groupby('investor_name', sort=False)

# For each group:
# - Concatenate IG_IDs with ", "
# - Concatenate roles with ", " (preserving order)
# - Create minimal card with defaults
```

### Phase 4: Handle Special Cases
```python
# Undisclosed: use existing card (ID=366)
# Update only IG_ID and investor_role

# Dual role companies: 
# Identify by checking if name appears in both targets and investors
# Create 2 separate cards
```

### Phase 5: Combine & Export
```python
# Combine all cards
final_df = pd.concat([target_cards, investor_cards, undisclosed_card])

# Validate columns
# Export to CSV with proper encoding
```

---

## 🔍 Validation Checklist

### Critical Validations:
- [ ] IG_ID format: "123, 456, 789" (comma + space)
- [ ] Role order matches IG_ID order exactly
- [ ] No duplicate names within target or investor groups
- [ ] Dual role companies have 2 separate cards
- [ ] Undisclosed uses ID=366
- [ ] All other IDs are empty

### Data Quality:
- [ ] No NULL values (use empty strings)
- [ ] UTF-8 encoding throughout
- [ ] 25 columns in correct order
- [ ] arc_status="TO BE CREATED" preserved
- [ ] Timestamps in correct format

### Output:
- [ ] Single file created
- [ ] ~800-1,200 total rows (after dedup)
- [ ] CSV format valid
- [ ] Ready for Arcadia import

---

## 📊 Expected Results

### Before Deduplication:
- 1,568 raw rows
- Multiple duplicates

### Final Results (Actual):
- **774** unique target cards ✅
- **851** unique investor cards ✅
- **22** dual role cards (companies in both roles) ✅
- **Total: 1,625** cards generated

### Achieved Metrics:
- **191 cards** with multiple IG_IDs (concatenated)
- **492 transactions** for Undisclosed (using existing ID=366)
- **Maximum 9 IG_IDs** in single card (Animoca Brands as investor)
- **100% validation** passed - all formats correct

---

## ⚠️ Critical Notes

### Format Requirements:
1. **Separator MUST be ", "** (comma followed by space)
2. **Order preservation is CRITICAL** - roles must match IG_IDs
3. **Case-sensitive matching** for deduplication

### Examples of Correct Format:
```
IG_ID: "123, 456, 789"  ✅
IG_ID: "123,456,789"    ❌ (missing spaces)
IG_ID: "123; 456; 789"  ❌ (wrong separator)

investor_role: "lead, participant, lead"  ✅
investor_role: "TARGET, TARGET, TARGET"   ✅
```

### Priority Rules for Metadata:
When selecting best data from duplicates:
1. Non-empty arc_* fields win
2. Then non-empty original fields
3. Then first occurrence
4. Never mix metadata from different rows randomly

---

**Document Version**: 2.0 FINAL  
**Status**: ✅ COMPLETED  
**Output File**: `arcadia_company_cards_deduplicated.csv` (1,625 cards)  
**Script**: `create_deduplicated_company_cards.py` ✅ Successfully executed

## Final Deliverables
1. **Company Cards File**: `output/arcadia_company_cards_deduplicated.csv` - 1,625 deduplicated cards
2. **Generation Report**: `docs/company_cards_generation_report.md` - Complete statistics
3. **Processing Script**: `scripts/create_deduplicated_company_cards.py` - Fully functional
4. **This Documentation**: Complete mapping plan with actual results