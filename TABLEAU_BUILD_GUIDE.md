# Tableau Workbook Guide

The implemented Tableau deliverables are:

- `tableau/ESG_Data_Quality_Regulatory_Readiness.twbx` — portable packaged workbook.
- `tableau/ESG_Data_Quality_Regulatory_Readiness.twb` — readable workbook source.
- `tableau/Data/` — local CSV sources used by the loose workbook.

## Dashboards

1. `01 | Executive Data Quality Overview`
2. `02 | Data Quality Analysis`
3. `03 | Regulatory Readiness`
4. `04 | Exceptions and Remediation`

## Refresh

Run the data pipeline first, then rebuild the Tableau package:

```bash
python python/esg_data_quality_engine.py
python python/build_tableau_workbook.py
```

The build uses Tableau chart templates for worksheet generation, assembles the dashboards, validates the `.twb` structure, and packages the data sources into the `.twbx`.

## Interpretation

- Percentages stored in CSV files are already expressed on a 0–100 scale.
- `Record_Pass_Rate` and `Data_Quality_Score` are intentionally different measures.
- `Readiness_Score` is a portfolio-designed preparation indicator, not a legal compliance status.
- Missing-year records appear in overall controls but not reporting-year trends.

