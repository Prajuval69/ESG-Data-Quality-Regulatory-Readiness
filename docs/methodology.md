# Methodology

## Data-quality scoring

Portfolio-defined score = 30% Completeness + 30% Validity + 25% Consistency + 15% Traceability.

- Completeness uses expected company-year-metric combinations.
- Validity excludes missing values, invalid units, negative emissions, missing reporting years, and missing GHG scopes.
- Consistency excludes duplicate business keys and 1.5×IQR outlier flags.
- Traceability requires a source reference.

Record status is `Valid` only when no automated exception flag is triggered. The record pass rate is therefore distinct from the weighted score. Outliers are review signals and may be legitimate extreme values.

## Readiness screening

Readiness Score = 70% selected requirement coverage + 30% data-quality score. It is calculated at company-year level across nine selected data areas, then aggregated for portfolio reporting.

The readiness framework is a portfolio control model, not a legal compliance determination. Timeliness and exception aging are omitted because the synthetic source does not contain reliable event or submission dates.
