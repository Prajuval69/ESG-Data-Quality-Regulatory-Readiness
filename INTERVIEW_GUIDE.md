# Interview Guide
1. **Problem:** Create a repeatable control layer between ESG source data and reporting.
2. **Why quality:** Reporting conclusions depend on reliable, comparable and traceable inputs.
3. **Rules:** Started with a controlled metric/unit dictionary and translated failure modes into deterministic checks.
4. **Duplicates:** Company + year + metric business key.
5. **Outliers:** 1.5×IQR within each metric; review signal, not automatic error.
6. **Score:** 30% completeness, 30% validity, 25% consistency, 15% traceability.
7. **Scope 1/2/3:** Core GHG categories and useful climate-data control examples.
8. **Completeness vs validity:** Existence of expected data vs conformance to defined rules.
9. **Readiness matrix:** Turns data availability into actionable reporting-preparation gaps.
10. **Limitations:** Synthetic data, simplified rules, no legal determination.
11. **Scale:** Governed pipelines, source IDs, workflow, audit history and enterprise BI.
12. **Alteryx/Tableau Prep:** Repeatable low-code cleansing, joins and standardization.
13. **AI:** Exception classification, source extraction and summaries alongside deterministic controls.
14. **Conflicting sources:** Preserve source values, apply documented precedence, flag material conflicts and route for review.
15. **Critical issue:** Explain metric, impact, evidence, owner and immediate remediation.
