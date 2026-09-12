# Data Dictionary
| Field | Definition | Data Type | Example | Validation Requirement |
|---|---|---|---|---|
| Record_ID | Unique synthetic record ID | Text | R0001 | Required |
| Company | Synthetic entity | Text | Apex Manufacturing | Controlled list |
| Industry | Industry grouping | Text | Manufacturing | Controlled list |
| Country | Country grouping | Text | India | Controlled list |
| Reporting_Year | Reporting period | Integer | 2025 | Required |
| ESG_Category | ESG topic | Text | Climate | Reference-aligned |
| Metric | ESG metric | Text | Scope 1 Emissions | Reference lookup |
| Scope | GHG classification | Text | Emissions | Required for emissions |
| Value | Reported value | Numeric/Text | 25000 | Null/range/type checks |
| Unit | Reported unit | Text | tCO2e | Must match reference |
| Source_Type | Source type | Text | Internal ESG System | Traceability context |
| Source_Reference | Source identifier | Text | SRC-2025-01 | Required for traceability |
| Required | Portfolio required flag | Boolean | True | Controlled |
| Expected_Unit | Reference unit | Text | tCO2e | Reference lookup |

## Analytical output fields

| Field | Definition | Grain |
|---|---|---|
| Record_Pass_Rate | Percentage of records with no automated exception | Portfolio, company, or company-year |
| Completeness_Pct | Available required company-year-metric combinations divided by expected combinations | Portfolio, company, year, or metric |
| Validity_Pct | Percentage of records without defined validity failures | Portfolio, company, or company-year |
| Consistency_Pct | Percentage of records without duplicate or IQR-outlier flags | Portfolio, company, or company-year |
| Traceability_Pct | Percentage of records with a source reference | Portfolio, company, or company-year |
| Data_Quality_Score | 30/30/25/15 weighted portfolio quality score | Portfolio, company, or company-year |
| Readiness_Score | 70% selected requirement coverage + 30% data-quality score | Company-year or company |
| Regulatory_Coverage_Pct | Availability across nine selected readiness data areas | Company-year or company |
| High_Risk_Gap_Count | Missing Scope 1, 2, or 3 requirement instances | Company-year or company |
