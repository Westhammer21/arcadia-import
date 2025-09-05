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
| **Company Segment** | `segment` | ForeignKey | **Optional field** (`null=True`, `blank=True`). Links to `Segment` model. **Visibility:** Only shown for "Strategic / CVC" company type when sector="Gaming (Content Development/Publishing)" (ID=1). **Constraint:** `on_delete=PROTECT` prevents deletion of referenced segments. **Conditional visibility:** Automatically shown/hidden based on sector selection via JavaScript. | **Gaming industry sub-categorization for strategic companies.** **Conditional field:** Only appears when Gaming sector is selected. **Typical values:** "Mobile Gaming", "PC Gaming", "Console Gaming", "VR Gaming", etc. **UI Control:** `show_hide_company_fields.js` controls visibility based on sector selection. **Business use:** Gaming industry specialization, sub-market analysis. **File:** `organizations/models/company.py:93-98`, `organizations/static/show_hide_company_fields.js` |
| **Company Features** | `features` | ManyToManyField | **Multiple selection field.** Links to `Feature` model, `blank=True` (optional). **Visibility:** Only shown for "Strategic / CVC" company type. **Usage:** Multiple feature tags can be assigned. **Typical values:** "AI/ML", "Blockchain", "Mobile Gaming", "VR/AR", etc. | **Strategic companies' technology/business feature tags.** **UI:** Multi-select widget allowing multiple feature assignments. **Field visibility:** Hidden for investor types, shown for Strategic/CVC companies. **Business use:** Technology categorization, feature-based search and filtering, market trend analysis. **File:** `organizations/models/company.py:100-104` |
| **Investor Specialization** | `specialization` | ForeignKey | **Required field for investor types.** Links to `Specialization` model with `PROTECT` deletion. **Default:** `get_default_specialization()`. **Visibility:** Only shown for "Venture Capital & Accelerators" and "Private Equity & Inst." company types. **Constraint:** `blank=False` makes it required when visible. | **Investor companies' specialization classification.** **Typical values:** "Early Stage", "Growth Stage", "Industry Specific", etc. **Field visibility:** Hidden for strategic companies, shown for investor types (VC/PE). **Business use:** Investor categorization, matching with investment stages, portfolio analysis. **File:** `organizations/models/company.py:107-112` |
| **Investor AUM** | `aum` | DecimalField | **Precision:** `max_digits=8`, `decimal_places=1`. **Range:** 0.0 to 1,000,000.0 million USD. **Validation:** `MinValueValidator(Decimal("0.0"))`, `MaxValueValidator(Decimal("1000000.0"))`. **Visibility:** Only shown for "Venture Capital & Accelerators" and "Private Equity & Inst." company types. **Auto-clearing:** Automatically set to null for non-investor company types on save. **Optional field** (`null=True`, `blank=True`). | **Assets Under Management for investor companies in millions USD.** **Auto-clear logic:** When company type changes to Strategic/CVC or Other, AUM is automatically cleared via save() method. **Field visibility:** Hidden for strategic companies, shown for investor types. **Help text:** "AUM (in millions) from $0.0 to $1,000,000.0. This field is only applicable for companies of type 'Venture Capital & Accelerators' or 'Private Equity & Inst.'. For all other company types, this field will be automatically cleared on save." **File:** `organizations/models/company.py:115-127` |
| **Website** | `website` | URLField | **Optional field** (`null=True`, `blank=True`). Max length varies, must be valid URL format if provided. **Validation:** Django `URLField` validation ensures proper URL structure (http/https). **Model:** Part of `ContactDetails` model (one-to-one with Company, `related_name="contacts"`). | **Company's official website URL.** **Contact validation rule:** Company must have at least one contact method - website OR LinkedIn page OR CEO founder LinkedIn (validation in `ContactDetails` `clean()` method). **Business use:** Official company information source, due diligence, company verification. **Relationship:** `ContactDetails.website` field with `company.contacts.website` access pattern. **File:** `organizations/models/contact_details.py:9` |
| **LinkedIn Page** | `linkedin_page` | URLField | **Optional field** (`null=True`, `blank=True`). Must be valid URL format if provided. **Validation:** Django `URLField` validation for proper URL structure. **Model:** Part of `ContactDetails` model. **Contact validation rule:** At least one contact method required. | **Company's official LinkedIn corporate page.** **Business use:** Professional network verification, company following, employee discovery, business intelligence. **Access pattern:** `company.contacts.linkedin_page`. **Validation dependency:** Part of `ContactDetails` `clean()` method requiring at least one contact method. **File:** `organizations/models/contact_details.py:10` |
| **CEO Founder LinkedIn** | `ceo_founder_linkedin` | URLField | **Optional field** (`null=True`, `blank=True`). Must be valid URL format if provided. **Validation:** Django `URLField` validation for proper URL structure. **Model:** Part of `ContactDetails` model. **Contact validation rule:** At least one contact method required. | **LinkedIn profile of company's CEO or founder.** **Business use:** Leadership research, networking, due diligence, decision maker identification. **Access pattern:** `company.contacts.ceo_founder_linkedin`. **Validation dependency:** Part of `ContactDetails` `clean()` method requiring at least one contact method. **File:** `organizations/models/contact_details.py:11-13` |
| **Contact Email** | `email` | EmailField | **Optional field** (`blank=True`). Django `EmailField` with email format validation. **Model:** Part of `ContactDetails` model. **Validation:** Standard email format checking, can be blank. | **Company's primary contact email address.** **Email validation:** Standard Django email format validation ensures proper structure (user@domain.com). **Access pattern:** `company.contacts.email`. **Business use:** Official communication channel, automated notifications, business correspondence. **File:** `organizations/models/contact_details.py:14` |
| **Transactions Count** | `transactions_count` | PositiveIntegerField | **Auto-calculated field.** Default: 0. **Read-only:** Cannot be manually set. **Updates:** Automatically updated when transactions involving this company are created/modified. | **System-maintained count of transactions.** **Business use:** Performance optimization, quick reference for company activity level, filtering companies by transaction activity. **Auto-update:** Incremented/decremented automatically via transaction signals. **File:** `organizations/models/company.py:137-140` |
| **Search Index** | `search_index` | CharField | **Auto-generated field.** Max 2000 chars, `null=True`, `blank=True`, `editable=False`. **Content:** Comma-separated searchable text including name, also_known_as, hq_country, hq_region, website. **Special handling:** Shows "notenoughinformation" for country="XX". | **System-generated search optimization field.** **Auto-update:** Rebuilt on every save() operation with current field values. **Business logic:** Triggers IS_INCOMPLETE status when "notenoughinformation" detected. **Use:** Internal search functionality, data completeness validation. **File:** `organizations/models/company.py:155-162` |
| **Created Date** | `was_added` | DateTimeField | **Auto-generated field.** `auto_now_add=True`, cannot be modified. **Timezone:** Uses Django timezone settings. | **Company creation timestamp.** **Business use:** Audit trail, creation date tracking, reporting on company addition patterns. **Immutable:** Set once when company is created, never changes. **File:** `organizations/models/company.py:142` |
| **Modified Date** | `was_changed` | DateTimeField | **Auto-updated field.** `auto_now=True`, updates on every save. **Timezone:** Uses Django timezone settings. | **Last modification timestamp.** **Business use:** Audit trail, tracking recent changes, data freshness indicators. **Auto-update:** Updated automatically on every save() operation. **File:** `organizations/models/company.py:150` |

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
- Range validation: 0.0 ≤ AUM ≤ 1,000,000.0 million USD

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
| **Internal Information** | `internal_information` | CKEditor5Field | Optional, max 5000 chars, updated automatically for incomplete related companies | Internal team information field. Automatically updated when related companies have IS_INCOMPLETE status with [IS INCOMPLETE] line. Always available for manual editing and API access. |
| **Equity Value at Listing** | `equity_value_at_listing` | DecimalField | Conditional, max_digits=9, decimal_places=1, range: 0.0-100,000.0M | **Only for Listing (IPO/SPAC) transactions**. Hidden for other types via JavaScript. |
| **Transaction UUID** | `transaction_uuid` | UUIDField | Auto-generated via uuid.uuid4(), read-only | Unique identifier for tracking and API operations. |
| **Duplicate Detection Fields** | `signature_company`, `signature_date`, `signature_investor` | CharField | **System-generated fields** for duplicate detection. Auto-populated on save. `db_index=True` for performance. **Max length:** 255 chars each. **Content:** Company signature (target name processed), date signature (YYmonth format), investor signature (lead investors concatenated). | **Automated duplicate detection system.** **Purpose:** Identifies potential duplicate transactions using similarity algorithms. **Threshold:** 70% similarity triggers duplicate flag. **Business use:** Data quality control, preventing duplicate transaction entries. **File:** `transactions/models/transaction.py:185-203`, `transactions/utils/signature.py` |
| **Creation Date** | `created_at` | DateTimeField | **Auto-generated field.** `default=timezone.now`, cannot be modified. **Timezone:** Uses Django timezone settings. | **Transaction creation timestamp.** **Business use:** Audit trail, creation tracking, temporal analysis of transaction entry patterns. **Immutable:** Set once when transaction is created. **File:** `transactions/models/transaction.py:207` |

### **3.2 Advanced Business Logic Systems**

#### **3.2.1 Automated Signal-Based Business Rules**

**Location:** `transactions/signals.py`

The Arcadia system implements sophisticated automated business logic through Django signals that trigger when transactions are created, modified, or deleted:

**Parent Company Auto-Update System:**
- **Trigger:** When M&A transactions are saved with APPROVED status
- **Business Logic:** Automatically determines and updates parent company relationships based on M&A ownership patterns
- **Impact:** Ensures company hierarchies reflect real-world acquisition relationships without manual intervention
- **Cascade Effect:** When M&A transactions are deleted, system reverts to previous M&A-based parent or manual setting

**Transaction Count Tracking:**
- **Trigger:** Any transaction creation, modification, or deletion involving a company
- **Business Logic:** Automatically maintains `transactions_count` field for each company
- **Impact:** Provides real-time activity metrics for companies without expensive database queries
- **Business Use:** Performance optimization for company listings, activity-based filtering and ranking

**ManyToMany Change Auditing:**
- **Trigger:** Changes to `other_investors` field in transactions
- **Business Logic:** Automatically logs investor changes in `other_investors_changes` field
- **Impact:** Maintains audit trail of investor modifications for compliance and analysis
- **Business Use:** Tracks investor relationship changes over time, regulatory compliance

#### **3.2.2 AI-Powered Duplicate Detection System**

**Location:** `organizations/utils/similarity_checker.py`

The system employs a sophisticated two-stage company name validation process that combines algorithmic and AI-powered analysis:

**Stage 1 - Algorithmic Similarity:**
- **Method:** Jaro-Winkler similarity algorithm with 89% threshold
- **Business Logic:** Identifies potential company name duplicates using string similarity
- **Impact:** Prevents obvious duplicate company entries during data import and manual creation

**Stage 2 - AI Validation:**
- **Trigger:** When algorithmic similarity is 89-99% (not exact match)
- **Method:** AI system analyzes company names using dedicated prompts to determine if they represent the same entity
- **Business Logic:** AI receives base company name + "also known as" names and candidate name for comparison
- **Decision Process:** AI responds with YES (duplicate) or NO (different entities)
- **Impact:** Sophisticated duplicate detection that understands business naming conventions, abbreviations, and industry-specific variations

**Business Benefits:**
- **Data Quality:** Maintains clean company database by preventing duplicate entries
- **Import Automation:** Enables large-scale Google Sheets imports with automatic duplicate handling
- **Relationship Management:** During import, similar names (single match) are automatically added to existing company's "Also Known As" field
- **Audit Trail:** All AI duplicate checking requests and responses are logged for transparency

#### **3.2.3 Transaction Signature & Duplicate Prevention**

**Location:** `transactions/utils/signature.py`

The system automatically generates unique signatures for each transaction to identify potential duplicates:

**Signature Components:**
- **Company Signature:** Processed target company name (normalized)
- **Date Signature:** Year-month format of announcement date
- **Investor Signature:** Concatenated lead investor names

**Duplicate Detection Logic:**
- **Threshold:** 70% similarity between transaction signatures triggers duplicate validation
- **Business Impact:** Prevents duplicate transaction entries that could skew financial analysis
- **Temporal Weighting:** Similar transactions within close time periods receive higher similarity scores
- **Override Capability:** Users can override duplicate warnings with confirmation for legitimate similar transactions

#### **3.2.4 Email Notification System**

**Location:** `properties/notifications.py`

The system maintains an automated email notification system for transaction approvals:

**Notification Triggers:**
- **Business Logic:** Automatically sends emails when transactions require approval
- **Target Audience:** Administrators and approval team members (Group ID=4)
- **Content:** HTML-formatted emails with transaction details and direct links to admin interface

**Email Distribution Logic:**
- **Group-Based:** Uses Django Groups to determine email recipients
- **Logging:** All email sends are tracked in `EmailSendLog` model for audit purposes
- **Business Impact:** Ensures timely review and approval of transactions, maintains approval workflow efficiency

**Unapproved Transaction Tracking:**
- **Function:** `get_unapproved_transactions()` identifies pending transactions
- **Business Use:** Dashboard metrics, workflow management, ensuring no transactions are overlooked

### **3.3 Transaction Type Categories & Lead Investor Requirements**

**Source:** `transactions/utils/utils.py` - TRANSACTION_TYPE_MAPPING

| Transaction Type | Transaction Category | Lead Investors Required | Special Logic |
|------------------|---------------------|------------------------|---------------|
| **M&A Category** |
| `"m&a control (incl. lbo/mbo)"` | `"M&A"` | 1-3 required | **Triggers parent company update**. Typically ≥50% stake. |
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

### **3.4 Advanced Validation Framework**

#### **3.4.1 Business Rule Validation System**

**Location:** `transactions/validators.py`

The Arcadia system enforces comprehensive validation rules that maintain data integrity and business logic compliance:

**Date Range Validation:**
- **Rule:** All transaction dates must fall between 2000-01-01 and current date
- **Business Impact:** Prevents historical data errors and future-dated transactions that could skew analysis
- **Application:** Applies to announcement_date, closed_date, and any other date fields

**Financial Value Constraints:**
- **Range:** $0.0 to $100,000.0 million USD for all financial fields
- **Business Logic:** Establishes realistic bounds for transaction sizes and valuations
- **Impact:** Prevents data entry errors that could distort financial analysis and reporting

**Description Content Validation:**
- **Word Count:** 10-150 words required for transaction descriptions
- **HTML Stripping:** Uses `strip_tags()` to count actual content words, not HTML markup
- **Business Purpose:** Ensures sufficient detail for analysis while preventing overly verbose entries

**MA Comments Validation:**
- **Character Limit:** Maximum 3,000 characters for M&A-specific comments
- **Word Limit:** Maximum 50 words for concise commentary
- **Business Use:** Structured approach to M&A transaction documentation

#### **3.4.2 IS_INCOMPLETE Status Management**

**Business Logic:** The system automatically manages data completeness through the IS_INCOMPLETE status, which cascades through related entities:

**Company-Level Triggers:**
- **Automatic Assignment:** When country="XX" (notenoughinformation) or required data is missing
- **Search Index Impact:** When search_index contains "notenoughinformation" text
- **Business Effect:** Companies with incomplete data are flagged for data enrichment

**Transaction-Level Cascade:**
- **Propagation Logic:** Transactions automatically inherit IS_INCOMPLETE status when any related company (target, lead investors, other investors) becomes incomplete
- **Internal Information Update:** System automatically adds `[IS INCOMPLETE]` notation to internal_information field
- **Recovery Process:** When all related companies become complete, transaction status reverts to previous state and `[IS INCOMPLETE]` notation is removed

**Business Benefits:**
- **Data Quality Control:** Maintains system-wide data completeness standards
- **Workflow Management:** Flags incomplete records for data team attention
- **Automated Recovery:** Self-correcting system that removes incomplete flags when data is enriched

#### **3.4.3 Google Sheets Integration Business Logic**

**Location:** `organizations/management/commands/import_companies_from_gsheet.py`

The system supports large-scale company data import with sophisticated business rules:

**Status Assignment Logic:**
- **IMPORTED:** Successfully imported companies with complete data
- **IS_INCOMPLETE:** Companies with data quality issues (website problems, country lookup failures)
- **DUPLICATE:** Exact name matches with existing companies (100% similarity)
- **ERROR:** Critical import failures requiring manual intervention

**Similarity-Based Import Decisions:**
- **100% Match:** Skipped as duplicate, logged in Google Sheet
- **85-99% Single Match:** Automatically added to existing company's "Also Known As" field
- **85-99% Multiple Matches:** Flagged as "PROBLEM: SIMILAR COMPANIES" for manual review
- **<85% Similarity:** Imported as new company

**Business Benefits:**
- **Automated Deduplication:** Prevents duplicate company creation during bulk imports
- **Relationship Enhancement:** Automatically enriches existing companies with alternative names
- **Data Quality Feedback:** Google Sheet logging provides immediate feedback on import results

### **3.5 Transaction Business Rules (Implemented in models/transaction.py)**

#### **IS_INCOMPLETE Status Auto-Assignment:**
The system automatically sets transaction status to IS_INCOMPLETE when:
- Target company has status IS_INCOMPLETE
- Any lead investor has status IS_INCOMPLETE  
- Any other investor has status IS_INCOMPLETE
- Automatically appends/updates `[IS INCOMPLETE]` line in internal_information field
- When all related companies become complete, status reverts to previous or ON_APPROVAL
- The `[IS INCOMPLETE]` line is removed from internal_information when status reverts

#### **Automatic Closed Date Logic:**
For non-M&A and non-Public offering transactions:
- `closed_date` is automatically set equal to `announcement_date`
- `not_closed_yet` is always set to False
- These fields are not visible/editable for these transaction categories

#### **M&A Transaction Size Auto-Calculation:**
```python
# For M&A transactions only
transaction_size = maximum_enterprise_value × (upfront_stake_acquired / 100)
```
- Only applies to M&A category transactions
- Calculated automatically when MADetails are saved
- Cannot be manually overridden for M&A transactions
- Uses rounded values (1 decimal place precision)

#### **Duplicate Detection Logic:**
- Signatures generated automatically on save: company, date, investor components
- 70% similarity threshold triggers potential duplicate validation  
- Uses sophisticated similarity algorithm with temporal weighting
- Prevents creation of transactions above similarity threshold
- Background duplicate checking for existing transactions

### **3.6 AI Module Integration**

**Location:** `ai_module/` - Complete AI integration system

The Arcadia platform incorporates sophisticated AI capabilities for enhanced data processing and business logic automation:

#### **AI-Powered Business Operations:**

**Duplicate Company Detection:**
- **Business Function:** AI analyzes company names to determine if they represent the same business entity
- **Process:** When algorithmic similarity (89-99%) is detected, AI receives company names and "also known as" variations for intelligent comparison
- **Business Impact:** Prevents duplicate company entries while understanding business naming conventions, abbreviations, and industry variations
- **Decision Making:** AI responds with YES/NO determinations that directly impact import and validation workflows

**Prompt Management System:**
- **Business Logic:** Centralized AI prompt management through `AIPrompt` model with dedicated admin interface
- **Version Control:** Different AI prompts for various business functions (duplicate detection, content analysis, etc.)
- **Audit Trail:** All AI interactions logged in `AILog` model for transparency and analysis

**AI Service Architecture:**
- **Factory Pattern:** Extensible design allowing integration with multiple AI providers (currently OpenAI)
- **Error Handling:** Sophisticated error management for AI service failures with fallback procedures
- **Business Continuity:** System functions continue even if AI services are temporarily unavailable

#### **Business Benefits:**
- **Automated Decision Making:** AI handles complex business logic decisions that would require manual review
- **Scalability:** Enables processing of large datasets with intelligent duplicate detection
- **Quality Assurance:** Maintains high data quality standards through AI-powered validation
- **Audit Compliance:** Complete logging of AI decisions for regulatory and business review

### **3.7 Custom Admin Interface Enhancements**

**Location:** Various admin.py files and custom templates

The Arcadia system features extensively customized Django admin interface that supports complex business workflows:

#### **Dynamic Field Visibility:**
- **Business Logic:** Company and transaction forms automatically show/hide fields based on selections
- **Company Types:** Strategic/CVC companies show different fields than VC/PE firms
- **Transaction Types:** Form fields adjust based on transaction category selection
- **Business Impact:** Streamlined data entry with relevant fields only, reducing errors and improving user experience

#### **Parent Company Management:**
- **Auto-Determination Display:** Admin interface clearly shows when parent company is auto-determined by M&A transactions
- **Read-Only Protection:** Fields become read-only with explanatory text when business rules prevent manual editing
- **Visual Indicators:** Clear messaging about automatic vs. manual parent company assignments

#### **Advanced Inline Management:**
- **M&A Details:** Sophisticated inline editing for M&A-specific transaction details
- **Financial Data:** Structured financial information management with automatic calculations
- **Investment Details:** Investment-specific data management with validation

#### **Custom Template Tags:**
- **Business Functions:** Custom template filters for form field error handling and display logic
- **Error Management:** Enhanced error display with field-specific formatting
- **Data Presentation:** Specialized formatting for financial data, dates, and business metrics

### **3.8 M&A Details Model**

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

### **3.5 Investment Details Model**

**Location:** `transactions/models/investment_details.py`

For Early-stage and Late-stage investment transactions:

For Early-stage and Late-stage investment transactions:

| Field Name | Variable Name | Type | Constraints & Validation | Business Logic |
|------------|---------------|------|-------------------------|----------------|
| **Transaction** | `transaction` | OneToOneField | Required, links to Transaction, on_delete=CASCADE | Primary relationship to transaction. |
| **Investment Details Comments** | `investment_details_comments` | TextField | Optional, max 3000 chars | Investment-specific notes and details. |
| **Post Money Enterprise Value** | `post_money_enterprise_value` | DecimalField | Required, max_digits=8, decimal_places=1, must be > 0 | Company valuation after investment. |
| **Stake Acquired** | `stake_acquired` | DecimalField | Required, max_digits=5, decimal_places=2, must be > 0 | Percentage stake acquired by investors. |

### **3.6 Financial Data Model**

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

### **3.7 Transaction Signature & Duplicate Detection**

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

This documentation accurately reflects the actual implementation as confirmed through comprehensive codebase analysis, including all business logic, validation rules, API restrictions, and technical implementation details.

