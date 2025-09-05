# **Arcadia Platform – Comprehensive Technical Documentation**

Date: July 20, 2025  
Owner: [Sergei Evdokimov](mailto:sergeyevdokimov1@gmail.com)  

---

## **1. Arcadia Overview**

Arcadia is a comprehensive platform for tracking and managing company transactions across multiple industries, with a focus on mergers, acquisitions, investments, and public offerings. The system enforces strict business logic, data integrity constraints, and provides both web interface and API access with sophisticated duplicate detection and automated business rule enforcement.

**Key Features:**

* **Company Management:** Detailed company profiles with automated parent company determination and hierarchical relationships
* **Transaction Tracking:** Comprehensive M&A, investment, and public offering records with automated financial calculations
* **Automated Business Logic:** Parent company updates based on M&A transactions, transaction size calculations, and financial multiples
* **API Access:** RESTful API with JWT authentication and method restrictions (GET/POST only)
* **Data Integrity:** Extensive validation rules, duplicate detection algorithms, and audit trails
* **Role-based Access:** Different permission levels and restricted financial data access for specific user groups

---

## **2. Company Data Model & Business Logic**

### **2.1 Company Model Structure**

| Field Name | Variable Name | Type | Constraints & Validation | Business Logic |
|------------|---------------|------|-------------------------|----------------|
| **Status** | `status` | CharField | **Choices:** "ENABLED" (default), "DISABLED", "TO_DELETE", "IMPORTED", "IS_INCOMPLETE" (from `organizations/utils/choices.py`). **Constraints:** Cannot be set to TO_DELETE if company is used in APPROVED transactions as target, lead investor, or other investor. IS_INCOMPLETE cannot be set manually - automatically assigned when company has incomplete data (validation in `organizations/models/company.py` `clean()` method). **Validation:** System checks for approved transaction usage before allowing status change to TO_DELETE. System automatically sets IS_INCOMPLETE when "notenoughinformation" is detected in search_index or required fields are missing. | **Controls company visibility and business operations.** ENABLED companies are fully functional and searchable. DISABLED companies are hidden but data preserved. TO_DELETE marks for removal but cannot delete if transaction dependencies exist. IMPORTED indicates companies imported from external sources (Google Sheets). IS_INCOMPLETE is automatically set for companies with missing/incomplete required data (country="XX"/region="notenoughinformation" or other missing fields) and cannot be manually changed. **File:** `organizations/utils/choices.py`, `organizations/models/company.py` |
| **Company Name** | `name` | CharField | **Required field.** Max 100 chars, min 2 chars via `MinLengthValidator(2)`. **Unique constraint:** Must be globally unique across all companies. **Validation:** Cannot be empty, must meet length requirements. **Encoding:** Supports Unicode characters. | **Primary identifier for all company operations.** Used in transaction relationships, parent-child hierarchy, search operations. Name uniqueness enforced at database level. **File:** `organizations/models/company.py:31-37` |
| **Also Known As** | `also_known_as` | CharField | **Format:** Comma-separated alternative names, max 500 chars. **Unique constraint:** Each alternative name must be globally unique among ALL companies' names and alternative names (case-insensitive, ENABLED companies only). **Validation:** No double commas (,,), no duplicates within same field, global uniqueness check in `clean()` method (`organizations/models/company.py`). | **Used for search functionality only - not displayed in lists or cards.** Enables finding companies by alternative/former names. **Business rule:** Alternative name "ABC Corp" cannot exist if any company has name "ABC Corp" or includes "ABC Corp" in their `also_known_as` field. **File:** `organizations/models/company.py:179-220` |
| **Company Type** | `type` | ForeignKey | **Choices:** "Strategic / CVC" (default), "Venture Capital & Accelerators", "Private Equity & Inst.", "Other". **Required field.** Links to `CompanyType` model with `PROTECT` deletion. **Default:** `get_default_company_type()` returns "Strategic / CVC" (from `properties/utils.py`). | **Critical field controlling UI field visibility and business logic.** "Strategic / CVC" shows ownership, parent_company, sector, segment, features fields. "Venture Capital & Accelerators" and "Private Equity & Inst." show specialization and aum fields. "Other" shows basic fields only. **JavaScript visibility control:** `organizations/static/show_hide_company_fields.js` **File:** `properties/utils.py:15-16`, `organizations/models/company.py:46-51` |
| **Year of Foundation** | `founded` | IntegerField | **Range:** 1800 to current year (`timezone.now().year`). **Validators:** `MinValueValidator(1800)`, `MaxValueValidator(current_year)`. **Required field.** Accepts `null=True` but `blank=False` (admin requires input). | **Manual entry field for company establishment year.** Used in search/filtering and company profiles. **Historical constraint:** Minimum 1800 prevents invalid historical dates. **Dynamic validation:** Maximum year updates automatically each calendar year. **File:** `organizations/models/company.py:53-58` |
| **HQ Country** | `hq_country` | CountryField | **Django Countries field.** **Required field.** Uses ISO 3166-1 alpha-2 country codes (e.g., "US", "GB", "DE"). **UI:** Searchable dropdown with country names, supports `settings.COUNTRIES_FIRST` for priority ordering. `blank_label` is "(select country)". **Validation:** Must be valid ISO country code. | **Triggers automatic HQ Region population.** Every `save()` operation auto-fills `hq_region` via `get_country_region()` function (from `organizations/utils/utils.py`). **Cannot be manually overridden.** Country selection drives geographic categorization and regional analysis. **File:** `organizations/models/company.py:60-63`, `organizations/utils/utils.py` |
| **HQ Region** | `hq_region` | CharField | **Auto-calculated field.** Max 30 chars, `null=True`, `blank=False`. **Read-only:** Cannot be manually set via admin or API. **Source:** Automatically derived from `hq_country` via `get_country_region()` mapping function. **Help text:** "Automatically selected depending on the country". | **System-managed geographic classification.** Updated on every `save()` operation based on `hq_country` value. **Business use:** Regional filtering, geographic analysis, investor region matching. **Readonly in admin interface.** **Implementation:** `get_country_region()` function maps countries to predefined regions. **File:** `organizations/models/company.py:65-71`, `organizations/utils/utils.py` |
| **Company Ownership** | `ownership` | ForeignKey | **Optional field** (`null=True`, `blank=True`). Links to `OwnershipType` model with default "Private" via `get_default_ownership()` (from `properties/utils.py`). **Visibility:** Only shown for "Strategic / CVC" company type via JavaScript field control. **Constraint:** `on_delete=PROTECT` prevents deletion of referenced ownership types. | **Strategic companies' ownership structure classification.** **Typical values:** "Private", "Public", "Government", "Non-profit". **Field visibility:** Hidden for investor types (VC/PE), shown only for Strategic/CVC companies. **JavaScript control:** `show_hide_company_fields.js` toggles visibility based on company type selection. **File:** `organizations/models/company.py:73-79`, `properties/utils.py:7-8` |
| **Parent Company** | `parent_company` | ForeignKey (self) | **Self-referential ForeignKey.** Optional (`null=True`, `blank=True`), `on_delete=SET_NULL`. `related_name="children"`. **Circular reference prevention:** Cannot create A→B→A parent relationships. **Critical constraint:** Field becomes READ-ONLY if company is target in any M&A transaction - system auto-determines parent via M&A algorithm. | **Complex auto-determination for M&A targets.** **Algorithm:** 1) Find all APPROVED M&A transactions where company=target, 2) Order by announcement_date DESC, 3) For latest M&A: if "M&A control"→lead investor becomes parent; if "M&A minority"→first lead investor becomes parent. **Manual override:** Only allowed if NO M&A transactions exist. **Admin UI:** Field disabled with explanatory text if M&A transactions detected. **File:** `organizations/models/company.py:125-133`, `organizations/admin.py:177-188` |
| **Company Sector** | `sector` | ForeignKey | **Optional field** (`null=True`, `blank=True`). Links to `Sector` model. **Visibility:** Only shown for "Strategic / CVC" company type. **Typical values:** "Gaming (Content Development/Publishing)", "Technology", "Healthcare", etc. **Constraint:** `on_delete=PROTECT` prevents deletion of referenced sectors. | **Strategic companies' business sector classification.** **Special rule:** When sector="Gaming (Content Development/Publishing)" (ID=1), triggers visibility of Company Segment field. **Field visibility:** Hidden for investor types, shown for Strategic/CVC companies. **Business use:** Industry categorization, market analysis, sector-specific filtering. **File:** `organizations/models/company.py:81-86`, `organizations/static/show_hide_company_fields.js:42-44` |
| **Company Segment** | `segment` | ForeignKey | **Optional field** (`null=True`, `blank=True`). Links to `Segment` model. **Visibility:** Only shown for "Strategic / CVC" company type AND when sector="Gaming (Content Development/Publishing)" (ID=1). **Constraint:** `on_delete=PROTECT` prevents deletion of referenced segments. | **Gaming companies' specific segment classification.** **Conditional visibility:** Only appears when company type is "Strategic / CVC" AND sector is "Gaming (Content Development/Publishing)". **Business use:** Gaming industry subcategorization, specialized gaming market analysis. **JavaScript control:** `show_hide_company_fields.js` shows/hides based on sector selection. **File:** `organizations/models/company.py:87-93` |
| **Company Features** | `features` | ManyToManyField | **Multiple selection field.** Links to `Feature` model, `blank=True` (optional). **Visibility:** Only shown for "Strategic / CVC" company type. **Usage:** Multiple feature tags can be assigned. **Typical values:** "AI/ML", "Blockchain", "Mobile Gaming", "VR/AR", etc. | **Strategic companies' technology/business feature tags.** **UI:** Multi-select widget allowing multiple feature assignments. **Field visibility:** Hidden for investor types, shown for Strategic/CVC companies. **Business use:** Technology categorization, feature-based search and filtering, market trend analysis. **File:** `organizations/models/company.py:95-99` |
| **Investor Specialization** | `specialization` | ForeignKey | **Required field for investor companies** (`blank=False`). Links to `Specialization` model with `PROTECT` deletion. **Default:** `get_default_specialization()` returns "Generalist" (from `properties/utils.py`). **Visibility:** Only shown for "Venture Capital & Accelerators" and "Private Equity & Inst." company types. | **Investor companies' specialization focus.** **Typical values:** "Generalist", "Gaming", "Technology", "Healthcare", etc. **Field visibility:** Hidden for Strategic/CVC companies, shown for investor types. **Business use:** Investor categorization, matching investments to specializations, investment trend analysis. **File:** `organizations/models/company.py:101-107`, `properties/utils.py:11-12` |
| **Investor AUM** | `aum` | DecimalField | **Optional field** (`null=True`, `blank=True`). Max_digits=8, decimal_places=1. **Range:** 0.0 to 1,000,000.0 million USD via `MinValueValidator(0.0)`, `MaxValueValidator(1000000.0)`. **Visibility:** Only applicable for "Venture Capital & Accelerators" or "Private Equity & Inst." company types. | **Assets Under Management for investor companies.** **Auto-clearing logic:** Automatically set to null on save() for non-investor company types. **Help text:** "AUM (in millions) from $0.0 to $1,000,000.0. This field is only applicable for companies of type 'Venture Capital & Accelerators' or 'Private Equity & Inst.'. For all other company types, this field will be automatically cleared on save." **File:** `organizations/models/company.py:109-124` |
| **Transactions Count** | `transactions_count` | PositiveIntegerField | **Auto-calculated field.** Default=0, automatically updated via signals. **Read-only:** Cannot be manually set. **Calculation:** Sum of transactions where company appears as lead investor or other investor. | **System-managed count of company's transaction participation.** **Signal-driven updates:** Automatically recalculated when transactions are created, updated, or deleted via `transactions/signals.py`. **Business use:** Performance metrics, activity tracking, company ranking by transaction volume. **Implementation:** Updated by `update_company_transactions_count()` function. **File:** `organizations/models/company.py:125-127`, `transactions/signals.py` |
| **Created By** | `created_by` | ForeignKey | **Optional field** (`null=True`, `blank=True`). Links to `AUTH_USER_MODEL` with `SET_NULL` deletion. `related_name="created_company"`. **Auto-tracking:** User who created the company record. | **Audit trail for company creation.** **User attribution:** Tracks which user created the company record. **Access pattern:** `company.created_by`. **Business use:** Audit trails, data quality management, user activity tracking. **File:** `organizations/models/company.py:133-138` |
| **Was Added** | `was_added` | DateTimeField | **Auto-timestamp field.** `auto_now_add=True`, cannot be edited. **Automatically set:** On company creation to current timestamp. | **Creation timestamp for audit trails.** **Config integration:** Updates `config.LAST_ORGANIZATION_ADDED` via save() method. **Business use:** Audit trails, data creation tracking, system monitoring. **File:** `organizations/models/company.py:129-130` |
| **Modified By** | `modified_by` | ForeignKey | **Optional field** (`null=True`, `blank=True`). Links to `AUTH_USER_MODEL` with `SET_NULL` deletion. `related_name="modified_company"`. **Auto-tracking:** User who last modified the company record. | **Audit trail for company modifications.** **User attribution:** Tracks which user last modified the company record. **Access pattern:** `company.modified_by`. **Business use:** Audit trails, change management, user activity tracking. **File:** `organizations/models/company.py:140-146` |
| **Was Changed** | `was_changed` | DateTimeField | **Auto-timestamp field.** `auto_now=True`, updated on every save. **Automatically updated:** On any company modification to current timestamp. | **Last modification timestamp for audit trails.** **Config integration:** Updates `config.LAST_ORGANIZATION_CHANGED` via save() method. **Business use:** Audit trails, change tracking, system monitoring, cache invalidation. **File:** `organizations/models/company.py:131-132` |
| **Website** | `website` | URLField | **Optional field** (`null=True`, `blank=True`). Max length varies, must be valid URL format if provided. **Validation:** Django `URLField` validation ensures proper URL structure (http/https). **Model:** Part of `ContactDetails` model (one-to-one with Company, `related_name="contacts"`). | **Company's official website URL.** **Contact validation rule:** Company must have at least one contact method - website OR LinkedIn page OR CEO founder LinkedIn (validation in `ContactDetails` `clean()` method). **Business use:** Official company information source, due diligence, company verification. **Relationship:** `ContactDetails.website` field with `company.contacts.website` access pattern. **File:** `organizations/models/contact_details.py:9` |
| **LinkedIn Page** | `linkedin_page` | URLField | **Optional field** (`null=True`, `blank=True`). Must be valid URL format if provided. **Validation:** Django `URLField` validation for proper URL structure. **Model:** Part of `ContactDetails` model. **Contact validation rule:** At least one contact method required. | **Company's official LinkedIn corporate page.** **Business use:** Professional network verification, company following, employee discovery, business intelligence. **Access pattern:** `company.contacts.linkedin_page`. **Validation dependency:** Part of `ContactDetails` `clean()` method requiring at least one contact method. **File:** `organizations/models/contact_details.py:10` |
| **CEO Founder LinkedIn** | `ceo_founder_linkedin` | URLField | **Optional field** (`null=True`, `blank=True`). Must be valid URL format if provided. **Validation:** Django `URLField` validation for proper URL structure. **Model:** Part of `ContactDetails` model. **Contact validation rule:** At least one contact method required. | **LinkedIn profile of company's CEO or founder.** **Business use:** Leadership research, networking, due diligence, decision maker identification. **Access pattern:** `company.contacts.ceo_founder_linkedin`. **Validation dependency:** Part of `ContactDetails` `clean()` method requiring at least one contact method. **File:** `organizations/models/contact_details.py:11-13` |
| **Contact Email** | `email` | EmailField | **Optional field** (`blank=True`). Django `EmailField` with email format validation. **Model:** Part of `ContactDetails` model. **Validation:** Standard email format checking, can be blank. | **Company's primary contact email address.** **Email validation:** Standard Django email format validation ensures proper structure (user@domain.com). **Access pattern:** `company.contacts.email`. **Business use:** Official communication channel, automated notifications, business correspondence. **File:** `organizations/models/contact_details.py:14` |
| **Search Index** | `search_index` | CharField | **Auto-generated field.** Max 2000 chars, `null=True`, `blank=True`, `editable=False`. **Content:** Comma-separated searchable text including name, also_known_as, hq_country, hq_region, website. **Special handling:** Shows "notenoughinformation" for country="XX". | **System-generated search optimization field.** **Auto-update:** Rebuilt on every save() operation with current field values. **Business logic:** Triggers IS_INCOMPLETE status when "notenoughinformation" detected. **Use:** Internal search functionality, data completeness validation. **File:** `organizations/models/company.py:155-162` |

### **2.2 Company Business Rules (Implemented in models/company.py)**

#### **Parent Company Auto-Determination Algorithm:**
**Location:** `organizations/models/company.py` - Referenced by transaction signals
1. System finds all **APPROVED** M&A transactions where company is target
2. Filters for non-disabled transactions  
3. Orders by announcement_date (newest first)
4. For latest M&A transaction:
   - If "M&A control (incl. LBO/MBO)": Lead investor becomes parent
   - If "M&A minority" with multiple leads: First lead investor becomes parent
5. **Manual override prohibited** if M&A transactions exist
6. When M&A deleted: Reverts to next latest M&A transaction
7. If no M&A transactions exist: parent_company can be set manually

#### **AUM Field Logic (save() method):**
```python
# Auto-clears AUM for non-investor company types
if self.type and not is_investor_type(self.type.name):
    self.aum = None
```
- Only applicable for: "Venture Capital & Accelerators" or "Private Equity & Inst."
- Automatically cleared (set to null) for other company types on save
- Range validation: 0.0 < AUM ≤ 1,000,000.0 million USD

#### **Transactions Count Logic (signals.py):**
```python
def update_company_transactions_count(company):
    """Recalculate and update the transactions_count for a given company."""
    count = (
        Transaction.objects.filter(lead_investors=company).count()
        + Transaction.objects.filter(other_investors=company).count()
    )
    Company.objects.filter(pk=company.pk).update(transactions_count=count)
```
- Automatically calculated via signals when transactions are created, updated, or deleted
- Counts both lead investor and other investor participations
- Updated by `transaction_post_save`, `transaction_post_delete`, and `transaction_other_investors_changed` signal handlers

#### **Config Integration (save() method):**
```python
def save(self, *args, **kwargs):
    # Update global configuration timestamps
    if self.pk is None:
        config.LAST_ORGANIZATION_ADDED = self.was_added
    config.LAST_ORGANIZATION_CHANGED = self.was_changed
    # Auto-update HQ region based on country
    self.hq_region = get_country_region(self.hq_country)
    # Clear AUM for non-investor types
    if self.type and not is_investor_type(self.type.name):
        self.aum = None
    super().save(*args, **kwargs)
```
- Updates global configuration with last organization added/changed timestamps
- Automatically updates HQ region based on selected country
- Enforces AUM field clearing for non-investor company types

#### **Alternative Names Validation (clean() method):**
```python
# Each alternative name must be unique among ALL companies
current_akas = [x.strip().lower() for x in self.also_known_as.split(",") if x.strip()]
# Checks against both company names and other alternative names
```
- Each alternative name in `also_known_as` must be unique among ALL companies
- Case-insensitive comparison using `.lower()`
- Only applies to ENABLED companies
- Validates against both company names and other alternative names

#### **Status Change Validation:**
Companies cannot be set to TO_DELETE if they are used in APPROVED transactions as:
- Target company
- Lead investor  
- Other investor

#### **IS_INCOMPLETE Status Auto-Assignment:**
The system automatically sets company status to IS_INCOMPLETE when:
- Country field is set to "XX" (showing "notenoughinformation" in search_index)
- Required fields are missing or contain insufficient information
- Search index contains "notenoughinformation" text
- This status cannot be manually set - only system-assigned
- Related transactions are also marked as IS_INCOMPLETE when companies become incomplete

#### **Search Index Auto-Generation (save() method):**
```python
# Auto-generated field with searchable content
search_index = name + "," + also_known_as + "," + hq_country + "," + hq_region + "," + website
```
- Rebuilt automatically on every save() operation
- Contains comma-separated searchable text from key fields  
- Special handling: country="XX" becomes "notenoughinformation"
- Used for internal search functionality and completeness validation
- Triggers IS_INCOMPLETE status when "notenoughinformation" detected

#### **Company Name Similarity Validation:**
**Location:** `organizations/utils/validators.py` - `validate_company_name()`
```python
def validate_company_name(name, override_similar=False, instance=None):
    # 1. Exact match (case-insensitive) is always forbidden
    qs = Company.objects.filter(name__iexact=name)
    if instance and instance.pk:
        qs = qs.exclude(pk=instance.pk)
    if qs.exists():
        raise ValidationError("A company with this exact name already exists.")

    # 2. Similarity >= 89 (Jaro-Winkler) is forbidden unless override_similar is True
    similar_names = get_similar_names(name, instance=instance)
    if similar_names and not override_similar:
        similar_names_str = ", ".join(f"{n} ({s}%)" for n, s in similar_names)
        raise ValidationError(
            f"A company with a similar name already exists: {similar_names_str}. "
            "Please check the Force creation or editing option if you wish to continue."
        )
```
- **Exact matches** (case-insensitive) are always forbidden
- **Similarity ≥89%** (Jaro-Winkler algorithm) requires `override_similar=True` flag
- **Admin integration:** Company admin form includes "Force creation or editing" checkbox
- **API integration:** API accepts `override_similar` parameter for similar name handling

#### **Parent Company Read-Only Logic:**
**Location:** `organizations/admin.py` - `CompanyAdminForm.__init__()`
```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    instance = kwargs.get("instance")
    if instance and instance.pk:
        from organizations.service import has_ma_transaction_as_target

        if has_ma_transaction_as_target(instance.pk):
            parent_field = self.fields.get("parent_company")
            if parent_field:
                parent_field.disabled = True
                company_name = instance.name
                link = f"/admin/transactions/transaction/?q={company_name}"
                parent_field.help_text = (
                    "This field is read-only because this company is a Target Company in at least one M&A transaction. "
                    f"See <a href='{link}' target='_blank'>all related transactions</a>."
                )
```
- **Dynamic field disabling:** Parent company field becomes read-only if company is target in any M&A transaction
- **Visual feedback:** Help text provides link to view related M&A transactions
- **Business rule enforcement:** Prevents manual override of auto-determined parent companies

#### **Google Sheets Import Logic:**
**Location:** `organizations/management/commands/import_companies_from_gsheet.py`

When importing companies from Google Sheets, the system applies the following default values and rules:

**Import Status Assignment:**
- **Status:** Set to `IMPORTED` if no data issues exist
- **Status:** Set to `IS_INCOMPLETE` if website problems or country lookup failures occur

**Default Field Values:**
- **Name:** Taken from "Correct Target Name" column
- **Year of Foundation:** Taken from "Target Founded" column, defaults to `1800` if empty or invalid
- **Website:** Set to `"notenoughinformation.com"` if missing or invalid URL format
- **HQ Country:** Set to `"XX"` (code for notenoughinformation) if country lookup via pycountry fails
- **HQ Region:** Set to `"notenoughinformation"` when country is "XX"
- **Company Type:** Always set to "Strategic / CVC" (default type)
- **Ownership:** Always set to default ownership type
- **Specialization:** Always set to default specialization for all imported companies
- **AUM:** Always remains null (auto-cleared by save() logic for Strategic/CVC types)
- **Also Known As:** Taken from "Also Known As" column
- **Contact fields:** Always remain empty (Ownership, Parent Company, LinkedIn Page, CEO/Founder LinkedIn, Contact Email)

**Import Validation Logic:**
- **Duplicate Detection:** Uses exact name matching and similarity scoring (85%+ threshold)
- **Website Validation:** Must contain "." and no spaces to be considered valid
- **Country Validation:** Uses pycountry library for country code lookup
- **Sector/Segment Mapping:** From predefined dictionaries in import command
- **Feature Assignment:** Based on "AI" column (YES = AI/ML feature) and segment mapping

**Skip Logic:**
- Rows with STATUS = "IMPORTED" are automatically skipped during import
- Companies with 100% name similarity are marked as "DUPLICATE" and not imported
- Companies with 85-99% similarity (single match) get added to existing company's "Also Known As"
- Companies with 85-99% similarity (multiple matches) are marked as "PROBLEM: SIMILAR COMPANIES"

**Error Handling:**
- Website issues: Set to notenoughinformation.com, status becomes IS_INCOMPLETE
- Country issues: Set to "XX"/notenoughinformation, status becomes IS_INCOMPLETE  
- Critical errors: STATUS = "ERROR" in Google Sheet, import continues with next row
- All operations are logged to Google Sheet STATUS and LOG columns

---

## **3. Transaction Data Model & Business Logic**

### **3.1 Transaction Model Structure**

| Field Name | Variable Name | Type | Constraints & Validation | Business Logic |
|------------|---------------|------|-------------------------|----------------|
| **Status** | `status` | CharField | Choices: ON_APPROVAL, APPROVED, DISABLED, TO_DELETE, IS_INCOMPLETE. Default: ON_APPROVAL | Controls transaction visibility and business rule triggers. Only APPROVED transactions affect parent company logic. IS_INCOMPLETE is automatically set when related companies have incomplete data. |
| **Announcement Date** | `announcement_date` | DateField | Required, range: 2000-01-01 to today, default=timezone.now | Date of first official announcement. Validated by validate_date_range(). |
| **Target Company** | `target_company` | ForeignKey | Required, links to Company model, on_delete=PROTECT | The company receiving investment/being acquired. Cannot be deleted if referenced. |
| **Transaction Size** | `transaction_size` | DecimalField | Required, max_digits=8, decimal_places=1, range: 0.0-100,000.0M | **Auto-calculated for M&A**, manual for others. Validated by validate_financial_values(). |
| **Transaction Type** | `transaction_type` | CharField | Required, max 50 chars, choices from get_transaction_type_choices() | Determines transaction category and validation rules. |
| **Transaction Category** | `transaction_category` | CharField | Auto-filled, read-only, default=DEFAULT | Derived from transaction_type in business logic, not directly editable. |
| **Closed Date** | `closed_date` | DateField | Conditional, range: 2000-01-01 to today, validated by validate_date_range() | Required if not_closed_yet=False. Must be ≥ announcement_date. |
| **To Be Closed** | `not_closed_yet` | BooleanField | Default: False | If True, closed_date must be empty. |
| **Lead Investor/Acquirer** | `lead_investors` | ManyToManyField | Conditional requirements by transaction type | Links to Company model. See Lead Investor Requirements below. |
| **Other Investors** | `other_investors` | ManyToManyField | Optional, max 10 selections, help_text specifies limit | Additional participating investors. |
| **Other Investors Changes** | `other_investors_changes` | CharField | **System tracking field.** Max 255 chars, `blank=True`, `null=True`. **Purpose:** Tracks changes to ManyToMany other_investors field for audit purposes. | **ManyToMany change tracking.** **Business use:** Audit trail for investor changes, system logging. **Auto-populated:** Updated automatically when other_investors field changes. **File:** `transactions/models/transaction.py:153` |
| **Source URL** | `source` | URLField | Required, valid URL format | Must be official source of transaction information. |
| **Description** | `description` | CKEditor5Field | Required, validated by validate_word_count(), 10-150 words | Rich text description with word count validation using strip_tags(). |
| **Equity Value at Listing** | `equity_value_at_listing` | DecimalField | Conditional, max_digits=9, decimal_places=1, range: 0.0-100,000.0M | **Only for Listing (IPO/SPAC) transactions**. Hidden for other types via JavaScript. |
| **Transaction UUID** | `transaction_uuid` | UUIDField | Auto-generated via uuid.uuid4(), read-only | Unique identifier for tracking and API operations. |
| **Signature Company** | `signature_company` | CharField | Auto-generated, max_length=255, db_index=True | **Target company component of transaction signature for duplicate detection.** Format: `target_company.name.lower().replace(" ", "")`. Used by duplicate detection algorithm. |
| **Signature Date** | `signature_date` | CharField | Auto-generated, max_length=50, db_index=True | **Date component of transaction signature for duplicate detection.** Format: Last two digits of year + lowercase month (e.g., "24may"). Used by duplicate detection algorithm. |
| **Signature Investor** | `signature_investor` | CharField | Auto-generated, max_length=255 | **Lead investor component of transaction signature for duplicate detection.** Format: Concatenated lead investor names or "noleadinvestor". Used by duplicate detection algorithm. |
| **Created At** | `created_at` | DateTimeField | Auto-timestamp, default=timezone.now | **Transaction creation timestamp.** Used for audit trails and chronological ordering. |

### **3.2 Transaction Type Categories & Lead Investor Requirements**

**Source:** `transactions/utils/utils.py` - TRANSACTION_TYPE_MAPPING

| Transaction Type | Transaction Category | Lead Investors Required | Special Logic |
|------------------|---------------------|------------------------|---------------|
| **M&A Category** |
| `"m&a control (incl. lbo/mbo)"` | `"M&A"` | **Exactly 1 required** | **Triggers parent company update**. Typically ≥50% stake. |
| `"m&a minority"` | `"M&A"` | 1-3 required | **Triggers parent company update**. First investor becomes parent. |
| **Early-stage Investments** |
| `"accelerator / grant"` | `"Early-stage investment"` | 1-3 required | Very early funding stage. |
| `"pre-seed"` | `"Early-stage investment"` | 1-3 required | Before product development. |
| `"seed"` | `"Early-stage investment"` | 1-3 required | Initial funding round. |
| `"series a"` | `"Early-stage investment"` | 1-3 required | First significant VC round. |
| `"undisclosed early-stage"` | `"Early-stage investment"` | 1-3 required | Non-disclosed early round. |
| **Late-stage Investments** |
| `"series b"` | `"Late-stage investment"` | 1-3 required | Growth funding. |
| `"series c"` | `"Late-stage investment"` | 1-3 required | Expansion capital. |
| `"series d"` | `"Late-stage investment"` | 1-3 required | Pre-IPO funding. |
| `"series e"` | `"Late-stage investment"` | 1-3 required | Additional late-stage. |
| `"growth / expansion (not specified)"` | `"Late-stage investment"` | 1-3 required | General growth capital. |
| `"undisclosed late-stage"` | `"Late-stage investment"` | 1-3 required | Non-disclosed late round. |
| **Public Offerings** |
| `"fixed income"` | `"Public offering"` | 0-3 allowed (optional) | Debt instruments. |
| `"listing (ipo/spac)"` | `"Public offering"` | 0-3 allowed (optional) | **Equity Value at Listing field required**. |
| `"pipe"` | `"Public offering"` | 0-3 allowed (optional) | Private placement in public company. |
| **Other** |
| `"other"` | `"Other"` | 0-3 allowed (optional) | Miscellaneous transactions. |

### **3.3 M&A Details Model**

**Location:** `transactions/models/ma_details.py`

For M&A transactions, additional details are stored in the `MADetails` model with one-to-one relationship:

| Field Name | Variable Name | Type | Constraints & Validation | Business Logic |
|------------|---------------|------|-------------------------|----------------|
| **Transaction** | `transaction` | OneToOneField | Required, links to Transaction, on_delete=CASCADE | Primary relationship to transaction. |
| **Financial Advisors** | `financial_advisors` | ManyToManyField | Optional, max 3 selections (validated in admin) | Links to Company model for advisory services. |
| **Equity Value** | `equity_value` | DecimalField | Optional, max_digits=8, decimal_places=1, can be null | 100% equity value. Can be empty if not available. |
| **Upfront Enterprise Value** | `upfront_enterprise_value` | DecimalField | Required, max_digits=8, decimal_places=1, must be > 0 | Initial announced enterprise value. Required field. |
| **Upfront Stake Acquired** | `upfront_stake_acquired` | DecimalField | Required, max_digits=5, decimal_places=2, range: 0.0-100.0% | Percentage of company acquired. Required field. |
| **Maximum Enterprise Value** | `maximum_enterprise_value` | DecimalField | Auto-calculated, max_digits=8, decimal_places=1 | **Upfront EV + Maximum Earn Out** (or 0.0 if N/A). |
| **Maximum Earn Out** | `maximum_earn_out` | DecimalField | Conditional, max_digits=8, decimal_places=1, max 100,000.0M | Additional contingent payments. Disabled if is_maximum_earn_out_na=True. |
| **Is Maximum Earn Out N/A** | `is_maximum_earn_out_na` | BooleanField | Default: False | If True, earn-out field is disabled and treated as 0.0. |
| **Comments** | `comments` | TextField | Optional, max 3000 chars | Additional M&A-specific notes. |

**Auto-calculation Logic (save() method):**
```python
# Maximum Enterprise Value calculation
if self.is_maximum_earn_out_na:
    self.maximum_earn_out = None
    max_earn_out_value = Decimal('0.0')
else:
    max_earn_out_value = self.maximum_earn_out or Decimal('0.0')

self.maximum_enterprise_value = self.upfront_enterprise_value + max_earn_out_value
```

### **3.4 Investment Details Model**

**Location:** `transactions/models/investment_details.py`

For Early-stage and Late-stage investment transactions:

| Field Name | Variable Name | Type | Constraints & Validation | Business Logic |
|------------|---------------|------|-------------------------|----------------|
| **Transaction** | `transaction` | OneToOneField | Required, links to Transaction, on_delete=CASCADE | Primary relationship to transaction. |
| **Investment Details Comments** | `investment_details_comments` | TextField | Optional, max 3000 chars | Investment-specific notes and details. |
| **Post Money Enterprise Value** | `post_money_enterprise_value` | DecimalField | Required, max_digits=8, decimal_places=1, must be > 0 | Company valuation after investment. |
| **Stake Acquired** | `stake_acquired` | DecimalField | Required, max_digits=5, decimal_places=2, must be > 0 | Percentage stake acquired by investors. |

### **3.5 Financial Data Model**

**Location:** `transactions/models/financial_data.py`

Multiple financial data records can be associated with M&A transactions:

| Category | Fields | Type | Access Control | Business Logic |
|----------|--------|------|----------------|----------------|
| **Revenue Metrics** | `gross_revenue_ltm`, `gross_revenue_nty` | DecimalField | First record: All users. Additional records: Group ID=7 only | Last Twelve Months and Next Twelve Months revenue. |
| **EBITDA Metrics** | `ebitda_ltm`, `ebitda_nty`, `cash_ebitda_cyo` | DecimalField | Restricted access for additional records | Earnings before interest, taxes, depreciation, and amortization. |
| **Financial Multiples** | `revenue_multiple_ltm`, `ebitda_multiple_ltm` | DecimalField | Auto-calculated based on enterprise value | **Automatic calculation when fields updated**. |
| **Other Metrics** | Various financial KPIs | DecimalField | Restricted access pattern | Additional financial performance indicators. |

**Access Control Logic:**
- **Regular Users**: Can see only the first financial data record per transaction
- **Group ID=7 Users**: Can see all financial data records for a transaction  
- **API Limitation**: Only exposes first financial data record regardless of user permissions

**Auto-calculation (save() method):**
```python
# Revenue multiple calculation
if self.gross_revenue_ltm and self.gross_revenue_ltm > 0:
    self.revenue_multiple_ltm = self.upfront_enterprise_value / self.gross_revenue_ltm

# EBITDA multiple calculation  
if self.ebitda_ltm and self.ebitda_ltm > 0:
    self.ebitda_multiple_ltm = self.upfront_enterprise_value / self.ebitda_ltm
```

### **3.6 Transaction Signature & Duplicate Detection**

**Location:** `transactions/utils/signature.py`

The system implements sophisticated duplicate detection using transaction signatures:

**Signature Components:**
1. **Company Signature**: `target_company.name.lower().replace(" ", "")`
2. **Date Signature**: Last two digits of year + lowercase month (e.g., "24may")  
3. **Investor Signature**: Lead investor names concatenated or "noleadinvestor"

**Similarity Calculation Algorithm:**
```python
def calculate_similarity_score(sig1, sig2):
    # Different weights based on temporal proximity
    if same_month_year:
        company_weight, date_weight, investor_weight = 0.55, 0.15, 0.30
    elif different_months_same_year:
        company_weight, date_weight, investor_weight = 0.40, 0.20, 0.40
    else:  # different_years
        company_weight, date_weight, investor_weight = 0.10, 0.10, 0.10
```

**Duplicate Detection Threshold:** 70% similarity triggers potential duplicate flag

---

## **3.2 Advanced Business Logic Systems**

### **3.2.1 Automated Signal-Based Business Rules**

**Location:** `transactions/signals.py`, `organizations/signals.py`

#### **Parent Company Auto-Updates**
**Trigger:** M&A transaction creation, approval, deletion, or status changes

**Algorithm Implementation:**
```python
def update_parent_company_from_latest_ma(target_company_id):
    """Auto-determine parent company from latest M&A transaction"""
    # 1. Find all APPROVED M&A transactions for target company
    ma_transactions = Transaction.objects.filter(
        target_company_id=target_company_id,
        status='APPROVED',
        transaction_type__in=['m&a control (incl. lbo/mbo)', 'm&a minority']
    ).exclude(status='DISABLED').order_by('-announcement_date')
    
    # 2. For latest M&A transaction:
    if ma_transactions.exists():
        latest_ma = ma_transactions.first()
        if latest_ma.transaction_type == 'm&a control (incl. lbo/mbo)':
            # Lead investor becomes parent
            parent = latest_ma.lead_investors.first()
        elif latest_ma.transaction_type == 'm&a minority':
            # First lead investor becomes parent (if multiple leads)
            parent = latest_ma.lead_investors.first()
        
        Company.objects.filter(pk=target_company_id).update(parent_company=parent)
    else:
        # No M&A transactions: clear parent (allows manual setting)
        Company.objects.filter(pk=target_company_id).update(parent_company=None)
```

**Business Rules:**
- Only **APPROVED** M&A transactions trigger parent updates
- **Latest transaction wins** (ordered by announcement_date DESC)
- **M&A control**: Lead investor automatically becomes parent company
- **M&A minority**: First lead investor becomes parent company
- **Manual override prohibited** when M&A transactions exist
- **Cascading updates**: Parent company changes affect all related systems

#### **Transaction Count Tracking**
**Real-time Maintenance:** Automatically updated via signals when transactions change

**Signal Handlers:**
```python
@receiver(post_save, sender=Transaction)
def transaction_post_save(sender, instance, created, **kwargs):
    """Update transaction counts when transaction created/modified"""
    update_company_transactions_count(instance.target_company)
    for lead_investor in instance.lead_investors.all():
        update_company_transactions_count(lead_investor)
    for other_investor in instance.other_investors.all():
        update_company_transactions_count(other_investor)

@receiver(m2m_changed, sender=Transaction.other_investors.through)
def transaction_other_investors_changed(sender, instance, action, pk_set, **kwargs):
    """Track ManyToMany other_investors changes for audit"""
    if action in ['post_add', 'post_remove']:
        # Update transaction counts for affected investors
        for company_id in pk_set:
            company = Company.objects.get(pk=company_id)
            update_company_transactions_count(company)
        
        # Log the change for audit trail
        if action == 'post_add':
            change_log = f"Added investors: {list(pk_set)}"
        else:
            change_log = f"Removed investors: {list(pk_set)}"
        
        Transaction.objects.filter(pk=instance.pk).update(
            other_investors_changes=change_log
        )
```

**Count Calculation Logic:**
```python
def update_company_transactions_count(company):
    """Recalculate and update transactions_count for a company"""
    count = (
        Transaction.objects.filter(lead_investors=company).count()
        + Transaction.objects.filter(other_investors=company).count()
    )
    Company.objects.filter(pk=company.pk).update(transactions_count=count)
```

#### **ManyToMany Change Auditing**
**Field:** `other_investors_changes` in Transaction model
**Purpose:** Track investor relationship changes for audit compliance

**Audit Trail Implementation:**
- **Automatic tracking** when investors added/removed from transactions
- **Change descriptions** logged in human-readable format
- **Timestamp correlation** with Simple History for complete audit trail
- **User attribution** via signal context and history records

### **3.2.2 AI-Powered Duplicate Detection System**

**Location:** `organizations/utils/ai_duplicate_detection.py`

#### **Two-Stage Detection Process**

**Stage 1: Algorithmic Similarity**
```python
def check_company_similarity(company_name, exclude_id=None):
    """Stage 1: Jaro-Winkler similarity check"""
    companies = Company.objects.filter(status='ENABLED')
    if exclude_id:
        companies = companies.exclude(pk=exclude_id)
    
    similar_companies = []
    for company in companies:
        # Check main name
        similarity = jaro_winkler_similarity(company_name.lower(), company.name.lower())
        if similarity >= 0.89:  # 89% threshold
            similar_companies.append((company, similarity))
        
        # Check alternative names
        if company.also_known_as:
            for alt_name in company.also_known_as.split(','):
                alt_similarity = jaro_winkler_similarity(company_name.lower(), alt_name.strip().lower())
                if alt_similarity >= 0.89:
                    similar_companies.append((company, alt_similarity))
    
    return similar_companies
```

**Stage 2: AI Business Decision Analysis**
```python
def ai_duplicate_analysis(company_name, similar_companies):
    """Stage 2: AI analysis of business naming conventions"""
    
    ai_prompt = f"""
    Analyze if "{company_name}" represents the same business entity as these existing companies:
    {format_similar_companies(similar_companies)}
    
    Consider:
    - Business naming conventions (Inc., Corp., Ltd., LLC variations)
    - Abbreviations and acronyms in company names  
    - Industry-standard naming patterns
    - Parent/subsidiary relationships
    - Regional variations of same company
    
    Respond with: SAME_ENTITY or DIFFERENT_ENTITY and brief explanation.
    """
    
    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": ai_prompt}]
    )
    
    return parse_ai_decision(response.content)
```

**Integration Points:**
- **Company creation/editing**: Automatic similarity check with AI validation
- **API endpoints**: `override_similar` parameter for forcing creation despite similarities
- **Admin interface**: "Force creation or editing" checkbox for manual override
- **Batch imports**: Intelligent duplicate handling during Google Sheets imports

#### **Duplicate Resolution Strategies**

**High Similarity (≥89%) Resolution:**
1. **Single Match + AI Confirms Same Entity**: Add to existing company's `also_known_as` field
2. **Single Match + AI Confirms Different**: Allow creation with warning
3. **Multiple Matches**: Flag as "PROBLEM: SIMILAR COMPANIES" for manual review
4. **Exact Match (100%)**: Always block creation, force use of existing company

**Medium Similarity (85-88%) Handling:**
- **Single Match**: Add to `also_known_as` field of existing company
- **Multiple Matches**: Flag for manual review
- **No AI Analysis**: Lower similarity handled by algorithmic rules only

### **3.2.3 Transaction Signature & Duplicate Prevention**

**Enhanced Duplicate Detection Algorithm:**

```python
def detect_transaction_duplicates(transaction):
    """Advanced duplicate detection with temporal weighting"""
    
    # Generate transaction signature
    signature = {
        'company': transaction.target_company.name.lower().replace(" ", ""),
        'date': f"{transaction.announcement_date.year % 100}{transaction.announcement_date.strftime('%b').lower()}",
        'investor': get_investor_signature(transaction.lead_investors.all())
    }
    
    # Find potentially similar transactions
    candidates = Transaction.objects.filter(
        signature_company__icontains=signature['company'][:10],
        announcement_date__year__in=[
            transaction.announcement_date.year - 1,
            transaction.announcement_date.year,
            transaction.announcement_date.year + 1
        ]
    ).exclude(pk=transaction.pk)
    
    # Calculate similarity scores with temporal weighting
    duplicates = []
    for candidate in candidates:
        similarity_score = calculate_weighted_similarity(signature, candidate)
        if similarity_score >= 0.70:  # 70% threshold
            duplicates.append((candidate, similarity_score))
    
    return sorted(duplicates, key=lambda x: x[1], reverse=True)
```

**Temporal Weighting Logic:**
```python
def calculate_weighted_similarity(sig1, sig2):
    """Calculate similarity with temporal proximity weighting"""
    
    # Determine temporal relationship
    date1 = parse_signature_date(sig1['date'])
    date2 = parse_signature_date(sig2['date'])
    
    if date1.year == date2.year and date1.month == date2.month:
        # Same month/year: Company name most important
        weights = {'company': 0.55, 'date': 0.15, 'investor': 0.30}
    elif date1.year == date2.year:
        # Same year, different month: Balanced weighting
        weights = {'company': 0.40, 'date': 0.20, 'investor': 0.40}
    else:
        # Different years: All components less important
        weights = {'company': 0.10, 'date': 0.10, 'investor': 0.10}
    
    # Calculate component similarities
    company_sim = jaro_winkler_similarity(sig1['company'], sig2['company'])
    date_sim = 1.0 if sig1['date'] == sig2['date'] else 0.0
    investor_sim = jaro_winkler_similarity(sig1['investor'], sig2['investor'])
    
    # Weighted total
    total_similarity = (
        company_sim * weights['company'] +
        date_sim * weights['date'] +
        investor_sim * weights['investor']
    )
    
    return total_similarity
```

### **3.2.4 Email Notification System**

**Location:** `core/notifications.py`

#### **Automated Approval Workflow**

**Trigger Events:**
- New transaction submitted (status: ON_APPROVAL)
- Transaction status changed to ON_APPROVAL
- Company with high similarity requires review
- Duplicate transaction detected above threshold

**Notification Recipients:**
- **Group ID=4**: Administrators with approval authority
- **Escalation**: Group ID=1 for critical issues or delayed approvals

**Email Template System:**
```python
def send_approval_notification(transaction, notification_type):
    """Send automated approval notifications to administrators"""
    
    # Get Group ID=4 users (administrators)
    admin_users = User.objects.filter(groups__id=4, is_active=True)
    
    context = {
        'transaction': transaction,
        'target_company': transaction.target_company.name,
        'transaction_size': transaction.transaction_size,
        'lead_investors': list(transaction.lead_investors.all()),
        'approval_url': f"{settings.BASE_URL}/admin/transactions/transaction/{transaction.pk}/",
        'notification_type': notification_type,
        'submission_date': transaction.created_at,
        'urgency_level': determine_urgency(transaction)
    }
    
    # Select appropriate email template
    if notification_type == 'new_submission':
        template = 'emails/transaction_approval_required.html'
        subject = f"New Transaction Approval Required: {transaction.target_company.name}"
    elif notification_type == 'similarity_detected':
        template = 'emails/duplicate_review_required.html'
        subject = f"Potential Duplicate Transaction: {transaction.target_company.name}"
    
    # Send to all administrators
    for admin in admin_users:
        send_mail(
            subject=subject,
            html_message=render_to_string(template, context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin.email],
            fail_silently=False
        )
```

**Escalation Logic:**
```python
def check_approval_escalation():
    """Daily job: Check for transactions requiring escalation"""
    
    # Find transactions pending approval for >48 hours
    cutoff_date = timezone.now() - timedelta(hours=48)
    overdue_transactions = Transaction.objects.filter(
        status='ON_APPROVAL',
        created_at__lt=cutoff_date
    )
    
    for transaction in overdue_transactions:
        send_escalation_notification(transaction)
        
def send_escalation_notification(transaction):
    """Escalate to Group ID=1 for overdue approvals"""
    escalation_users = User.objects.filter(groups__id=1, is_active=True)
    
    # Send urgent notification to senior administrators
    context = {
        'transaction': transaction,
        'days_pending': (timezone.now() - transaction.created_at).days,
        'admin_url': f"{settings.BASE_URL}/admin/transactions/transaction/{transaction.pk}/",
        'urgency': 'HIGH'
    }
    
    for user in escalation_users:
        send_mail(
            subject=f"URGENT: Transaction Approval Overdue - {transaction.target_company.name}",
            html_message=render_to_string('emails/escalation_notice.html', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email]
        )
```

**Integration with Business Logic:**
- **Signal-triggered**: Automatic sending when transaction status changes
- **Batch processing**: Daily escalation checks via scheduled tasks
- **User preferences**: Configurable notification settings per administrator
- **Audit trail**: All sent notifications logged for compliance tracking

---

## **4. API Access Control & Security**

### **4.1 Authentication & Authorization**

**Location:** `arcadia/settings.py` - REST_FRAMEWORK configuration

- **JWT Token Authentication**: Required for all API requests via `rest_framework_simplejwt.authentication`
- **Active Users Only**: Users must have `is_active=True`
- **Permission Inheritance**: API permissions match Django admin permissions
- **No Staff Requirement**: `is_staff` status not required for API access

### **4.2 API Method Restrictions**

**Location:** Transaction and Company viewsets

| Operation | Companies | Transactions | Status | Error Response |
|-----------|-----------|--------------|--------|----------------|
| **GET** | ✅ Allowed | ✅ Allowed | Full read access | N/A |
| **POST** | ✅ Allowed | ✅ Allowed | Create new records | N/A |
| **PUT** | ❌ **FORBIDDEN** | ❌ **FORBIDDEN** | HTTP 405 Method Not Allowed | `{"detail": "Method 'PUT' not allowed."}` |
| **PATCH** | ❌ **FORBIDDEN** | ❌ **FORBIDDEN** | HTTP 405 Method Not Allowed | `{"detail": "Method 'PATCH' not allowed."}` |
| **DELETE** | ❌ **FORBIDDEN** | ❌ **FORBIDDEN** | HTTP 405 Method Not Allowed | `{"detail": "Method 'DELETE' not allowed."}` |

**Implementation:**
```python
# In viewsets
def get_allowed_methods(self):
    return ['GET', 'POST', 'HEAD', 'OPTIONS']
```

### **4.3 Financial Data Access Control**

**Location:** Financial data admin and API serializers

- **Regular Users**: Can only see first financial data record per transaction
- **Group ID=7 Users**: Can see all financial data records for a transaction
- **API Limitation**: Only exposes first financial data record regardless of user permissions

---

## **5. Data Validation & Business Rules**

### **5.1 Field-Level Validation**

**Location:** `transactions/validators.py`

| Validation Type | Function | Rules | Implementation |
|----------------|----------|-------|----------------|
| **Date Range** | `validate_date_range()` | 2000-01-01 to today | Used for announcement_date, closed_date |
| **Financial Values** | `validate_financial_values()` | 0.0 to 100,000.0M USD | Used for transaction_size, enterprise values |
| **Word Count** | `validate_word_count()` | 10-150 words | Uses `strip_tags()` for description field |
| **URL Format** | Django URLField | Valid HTTP/HTTPS | Source field validation |

### **5.2 Model-Level Validation (clean() methods)**

#### **Transaction Validation:**
```python
def clean(self):
    # Closed date must be >= announcement date
    if self.closed_date and self.announcement_date:
        if self.closed_date < self.announcement_date:
            raise ValidationError(...)
    
    # Word count validation for description
    if self.description:
        word_count = len(strip_tags(self.description).split())
        if not (10 <= word_count <= 150):
            raise ValidationError(...)
```

#### **Company Validation:**
```python
def clean(self):
    # Alternative names uniqueness validation
    if self.also_known_as:
        current_akas = [x.strip().lower() for x in self.also_known_as.split(",")]
        # Check against all other companies...
    
    # Status change validation for companies used in approved transactions
    if self.pk and self.status != ENABLED:
        # Check if used in approved transactions...
```

### **5.3 Automatic Calculations**

#### **M&A Transaction Size (signals.py):**
```python
# For M&A transactions only
transaction_size = maximum_enterprise_value × (upfront_stake_acquired / 100)
```

#### **Maximum Enterprise Value (MADetails.save()):**
```python
if is_maximum_earn_out_na:
    max_earn_out_value = Decimal('0.0')
else:
    max_earn_out_value = maximum_earn_out or Decimal('0.0')

maximum_enterprise_value = upfront_enterprise_value + max_earn_out_value
```

#### **Financial Multiples (FinancialData.save()):**
```python
revenue_multiple_ltm = upfront_enterprise_value / gross_revenue_ltm
ebitda_multiple_ltm = upfront_enterprise_value / ebitda_ltm
```

---

## **6. System Architecture & Technical Implementation**

### **6.1 Technology Stack**

- **Backend**: Django 4.x with Django REST Framework
- **Database**: MySQL with Simple History for audit trails  
- **Authentication**: JWT tokens via `django-rest-framework-simplejwt`
- **Rich Text**: CKEditor 5 for description fields
- **Countries**: `django-countries` for country field handling
- **Audit**: `django-simple-history` for change tracking

### **6.2 Model Relationships**

```
Company (1) ←→ (Many) Transaction [target_company]
Company (Many) ←→ (Many) Transaction [lead_investors]  
Company (Many) ←→ (Many) Transaction [other_investors]
Company (1) ←→ (1) Company [parent_company, self-referential]
Transaction (1) ←→ (0..1) MADetails [M&A transactions only]
Transaction (1) ←→ (0..1) InvestmentDetails [Investment transactions only]
Transaction (1) ←→ (Many) FinancialData [M&A transactions only]
MADetails (Many) ←→ (Many) Company [financial_advisors]
```

### **6.3 Admin Interface Logic**

**Location:** `transactions/admin.py`

#### **Dynamic Inline Block Display:**
| Transaction Category | Inline Blocks Shown | Access Restrictions |
|---------------------|---------------------|-------------------|
| **M&A** | MADetails, FinancialData, RestrictedFinancialData | RestrictedFinancialData: Group ID=7 only |
| **Early-stage Investments** | InvestmentDetails | None |
| **Late-stage Investments** | InvestmentDetails | None |
| **Public Offerings** | None | None |
| **Other** | None | None |

#### **Dynamic Field Visibility (JavaScript):**
- **Equity Value at Listing**: Only shown for "listing (ipo/spac)" transaction type
- **Maximum Earn Out**: Disabled when is_maximum_earn_out_na checkbox is checked
- **Lead Investors**: Count validation based on transaction type

---

## **7. Taxonomy & Reference Data**

### **7.1 Company Type**

**Location:** `properties/models.py`

| Option | Description | Field Visibility Rules |
|--------|-------------|----------------------|
| Strategic / CVC | Strategic buyers or corporate venture capital investors | Shows ownership, sector fields |
| Venture Capital & Accelerators | VC firms or accelerators investing in early-stage companies | Shows specialization, AUM fields |
| Private Equity & Institutional | PE funds and institutional investors for later-stage companies | Shows specialization, AUM fields |
| Other | Non-gaming organizations, government, or unrelated entities | Basic fields only |

### **7.2 Transaction Type Categories**

**Location:** `transactions/utils/utils.py`

| Category | Transaction Types | Lead Investor Requirements |
|----------|-------------------|---------------------------|
| **M&A** | M&A control, M&A minority | 1-3 required, triggers parent company update |
| **Early-stage investment** | Accelerator/Grant, Pre-Seed, Seed, Series A, Undisclosed Early-stage | 1-3 required |
| **Late-stage investment** | Series B/C/D/E, Growth/Expansion, Undisclosed Late-stage | 1-3 required |
| **Public offering** | Fixed Income, Listing (IPO/SPAC), PIPE | 0-3 optional |
| **Other** | Other | 0-3 optional |

### **7.3 Geographic Regions**

**Location:** `organizations/utils/region_mapping.py`

Automatic region assignment based on country selection:
- **North America**: US, Canada, Mexico, etc.
- **Europe**: European Union countries, UK, Switzerland, etc.
- **Asia-Pacific**: China, Japan, South Korea, Australia, etc.
- **Other regions**: Middle East, Africa, Latin America, etc.

---

## **8. Error Handling & Audit Trail**

### **8.1 Validation Error Responses**

**API Format:**
```json
{
  "status": "error", 
  "code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "errors": {
    "field_name": ["Specific error message"]
  }
}
```

### **8.2 Method Restriction Responses**
```json
{
  "detail": "Method 'PUT' not allowed."
}
```

### **8.3 Audit Trail Implementation**

**Location:** `simple_history` integration in models

- **Simple History**: Tracks all changes to Company and Transaction models
- **User Attribution**: Automatic tracking via history records
- **Timestamp Tracking**: `was_added` and `was_changed` fields with auto_now/auto_now_add
- **Change Detection**: Manual tracking for M2M fields like `other_investors_changes`

### **8.4 Automated Business Processes (Signals)**

**Location:** `transactions/signals.py`

#### **Transaction Count Management:**
```python
@receiver(post_save, sender=Transaction)
def transaction_post_save(sender, instance, created, **kwargs):
    # Updates transactions_count for affected companies
    
@receiver(post_delete, sender=Transaction)  
def transaction_post_delete(sender, instance, **kwargs):
    # Decrements transactions_count when transaction deleted
    
@receiver(m2m_changed, sender=Transaction.other_investors.through)
def transaction_other_investors_changed(sender, instance, action, pk_set, **kwargs):
    # Updates count when other_investors relationship changes
```

#### **Parent Company Auto-Updates:**
- **Trigger events:** M&A transaction approval, deletion, or status changes
- **Algorithm:** Implemented in `organizations.service.update_parent_company_from_latest_ma()`
- **Signal integration:** Called automatically when M&A transactions are modified
- **Business rule:** Latest approved M&A transaction determines parent company

#### **Configuration Updates:**
- **Global timestamps:** Updates `config.LAST_ORGANIZATION_ADDED` and `config.LAST_ORGANIZATION_CHANGED`
- **Cache invalidation:** Triggers system-wide updates when organizations change
- **Monitoring integration:** Provides timestamps for system health monitoring

---

## **9. Testing Framework & Quality Assurance**

### **9.1 Factory Pattern Implementation**

**Location:** `transactions/tests/factories/` and `organizations/tests/factories.py`

- **factory_boy**: Used for creating consistent test objects
- **Available Factories**: CompanyFactory, TransactionFactory, MADetailsFactory, InvestmentDetailsFactory, FinancialDataFactory
- **Specialized Factories**: MAControlTransactionFactory, SeriesATransactionFactory with predefined transaction types
- **Helper Methods**: `CompanyFactory.create_investor()` for investor-specific companies

### **9.2 Test Structure & Coverage**

**Location:** `transactions/tests/` and `organizations/tests/`

- **Comprehensive Test Suite**: 25+ test files covering all major functionality
- **API Testing**: Separate test files for API endpoints and permissions
- **Business Logic Testing**: Dedicated tests for parent company updates, transaction calculations, duplicate detection
- **Validation Testing**: Tests for all validation rules and business constraints
- **Performance Testing**: Duplicate detection performance with large datasets

---

## **10. Key Business Rule Summary**

### **10.1 Parent Company Logic**
1. **Auto-updated** when M&A transactions are approved/deleted
2. **Manual override prohibited** if M&A transaction history exists
3. **Latest transaction wins** - most recent M&A determines parent
4. **Both M&A types trigger update** - control and minority transactions

### **10.2 Transaction Size Logic**
1. **M&A transactions**: Auto-calculated from maximum_enterprise_value × upfront_stake_acquired
2. **All other transactions**: Manual entry required
3. **Updates automatically** when M&A details change

### **10.3 Financial Data Access**
1. **First record**: Visible to all users
2. **Additional records**: Only visible to Group ID=7 users
3. **API exposure**: Always limited to first record only

### **10.4 Duplicate Detection**
1. **Automatic signature generation** for all transactions
2. **70% similarity threshold** for duplicate flagging  
3. **Weighted scoring** based on temporal proximity
4. **Performance optimized** with database indexing

---

## **11. Recent System Changes & Migration History**

### **11.1 Key Recent Migrations (2025)**

#### **Organizations App:**
- **0029_alter_company_aum_alter_historicalcompany_aum** (May 12, 2025): Updated AUM field with enhanced help text and decimal validation for investors
- **0028_company_parent_company_and_more** (April 28, 2025): Re-added parent_company field with self-referential relationship and SET_NULL deletion behavior
- **0027_remove_company_parent_company_and_more** (April 28, 2025): Temporarily removed parent_company field (likely for schema restructuring)

#### **Transactions App:**
- **0031_historicaltransaction_signature_company_and_more** (April 30, 2025): Added signature fields for duplicate detection (signature_company, signature_date, signature_investor) with database indexing
- **0037_financialdata_comments_cyo_and_more**: Added comment fields to FinancialData model for different time periods
- **0038_complete_financial_comments_migration**: Completed migration of financial comments structure
- **0039_remove_old_comment_fields**: Cleaned up old comment field structure

### **11.2 System Enhancements**

#### **Duplicate Detection System:**
- **Added April 30, 2025:** Comprehensive signature-based duplicate detection with database indexing
- **Performance optimization:** Indexed signature fields for fast similarity queries
- **Temporal weighting:** Different similarity thresholds based on transaction timing

#### **Financial Data Comments:**
- **Enhanced structure:** Separate comment fields for different time periods (CYO, LTM, NTM)
- **Migration completed:** Old comment structure migrated to new format
- **Improved organization:** Time-period specific commenting for better data organization

#### **AUM Field Improvements:**
- **Enhanced validation:** More precise decimal validation for Assets Under Management
- **Better help text:** Clearer instructions for users about AUM field usage
- **Auto-clearing logic:** Automatic field clearing for non-investor company types

### **11.3 Configuration & System Integration**

#### **Constance Configuration Integration:**
- **Global timestamps:** System tracks last organization added/changed for monitoring
- **Cache management:** Configuration updates trigger system-wide cache invalidation
- **Health monitoring:** Provides system health indicators through timestamp tracking

#### **Admin Interface Enhancements:**
- **Dynamic field visibility:** JavaScript-controlled field showing/hiding based on company type and sector
- **Parent company protection:** Automatic field disabling when M&A transactions exist
- **Similarity override:** Force creation option for similar company names

---

## **12. Key Business Rule Summary**

### **12.1 Parent Company Logic**
1. **Auto-updated** when M&A transactions are approved/deleted
2. **Manual override prohibited** if M&A transaction history exists
3. **Latest transaction wins** - most recent M&A determines parent
4. **Both M&A types trigger update** - control and minority transactions

### **12.2 Transaction Size Logic**
1. **M&A transactions**: Auto-calculated from maximum_enterprise_value × upfront_stake_acquired
2. **All other transactions**: Manual entry required
3. **Updates automatically** when M&A details change

### **12.3 Financial Data Access**
1. **First record**: Visible to all users
2. **Additional records**: Only visible to Group ID=7 users
3. **API exposure**: Always limited to first record only

### **12.4 Duplicate Detection**
1. **Automatic signature generation** for all transactions
2. **70% similarity threshold** for duplicate flagging  
3. **Weighted scoring** based on temporal proximity
4. **Performance optimized** with database indexing

### **12.5 Investment Details Auto-Calculation**
1. **Stake calculation**: Automatically calculated if transaction size and post-money EV are provided
2. **Formula**: `stake_acquired = (transaction_size / post_money_enterprise_value) × 100`
3. **Manual override**: Users can manually enter stake if auto-calculation not applicable

### **12.6 Company Validation Rules**
1. **Name uniqueness**: Exact matches forbidden, similarity ≥89% requires override
2. **Status protection**: Cannot delete companies used in approved transactions
3. **Parent company protection**: Auto-determined via M&A, manual editing blocked
4. **AUM field management**: Auto-cleared for non-investor company types

---

This documentation comprehensively reflects the current implementation as of July 19, 2025, including all recent migrations, business logic enhancements, validation rules, API restrictions, and technical implementation details. The system has evolved significantly with enhanced duplicate detection, improved financial data management, comprehensive validation rules, and sophisticated business logic automation.

