# Validation Rules

| Rule_ID   | Rule_Name               | Description                                       | Severity   | Logic                                          | Business_Impact                           |
|:----------|:------------------------|:--------------------------------------------------|:-----------|:-----------------------------------------------|:------------------------------------------|
| DQ001     | Missing Value           | Required metric has no reported value.            | High       | Value is null                                  | Completeness / reporting gap              |
| DQ002     | Duplicate Record        | Same company-year-metric appears more than once.  | Medium     | Duplicate company + year + metric key          | Duplicate reporting / reconciliation risk |
| DQ003     | Invalid Unit            | Reported unit differs from metric reference.      | Medium     | Unit != Expected_Unit                          | Comparability risk                        |
| DQ004     | Negative Emissions      | Emissions value is below zero.                    | Critical   | Emissions metric and Value < 0                 | Potentially material data integrity issue |
| DQ005     | Missing Reporting Year  | Reporting period is absent.                       | High       | Reporting_Year is null                         | Period traceability risk                  |
| DQ006     | Missing Scope           | Emissions record has no Scope classification.     | High       | Emissions metric and Scope is null             | GHG categorization risk                   |
| DQ007     | Unit Inconsistency      | A metric uses a non-standard unit in raw data.    | Medium     | Covered operationally by DQ003 in this version | Aggregation / comparability risk          |
| DQ008     | Outlier                 | Value is unusual relative to metric distribution. | Medium     | 1.5×IQR rule                                   | Requires source review                    |
| DQ009     | Missing Source          | Source reference is absent.                       | Low        | Source_Reference is null                       | Traceability risk                         |
| DQ010     | Required Metric Missing | Expected company-year-metric has no record.       | High       | Completeness matrix shows Availability=Missing | Reporting-readiness gap                   |

DQ007 is retained in the rule catalogue for conceptual completeness but consolidated with DQ003 in the generated exception log to avoid double-counting the same unit failure. DQ010 is represented in the completeness and readiness marts rather than the record-level exception log because no source record exists to attach it to.
