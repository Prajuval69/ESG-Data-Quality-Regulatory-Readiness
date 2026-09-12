# Validation Report

## Pipeline checks

- Raw record IDs are unique.
- The metric reference uses a unique metric key.
- The metric-reference join is validated as many-to-one.
- Automated tests confirm every intended failure type is represented.
- 223 source records reconcile to 188 records with no automated exception.
- The sum of record-level flags reconciles to 37 exception-log rows.
- The completeness matrix reconciles to 12 companies × 2 years × 12 required metrics = 288 rows.
- All quality and readiness scores remain between 0 and 100.

## KPI reconciliation

| Measure | Reconciled result |
|---|---:|
| Source records | 223 |
| Records with no automated exception | 188 |
| Record pass rate | 84.3% |
| Exception instances | 37 |
| High + critical exception instances | 11 |
| Completeness | 75.7% |
| Validity | 92.8% |
| Consistency | 92.4% |
| Traceability | 98.2% |
| Weighted data-quality score | 88.4% |

## Tableau checks

- The `.twb` passes the bundled Tableau structural validator with no errors.
- Workbook contents reconcile to 21 worksheets and 4 dashboard definitions.
- All worksheet and dashboard names are unique.
- All worksheet datasource references resolve to an included datasource.
- The `.twbx` package includes the workbook and all eight required CSV sources.
- The ZIP container integrity check passes.

## Excel checks

- The workbook was rebuilt from the same validated CSV marts used by Tableau.
- The Executive Summary formulas link to the Dashboard Data sheet.
- The final workbook scan found no `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, `#N/A`, `#NUM!`, `#NULL!`, `#SPILL!`, or `#CALC!` values.
- The Executive Summary was rendered and visually reviewed for clipping and legibility.

## Known environment limitation

Tableau Desktop and Tableau Server/Cloud were not exposed to the available computer-control environment. The workbook could therefore be generated, packaged, and structurally validated, but not opened for a native Tableau render or live filter/action test in this run. The static PNGs are source-backed previews, not exports from Tableau Desktop.
