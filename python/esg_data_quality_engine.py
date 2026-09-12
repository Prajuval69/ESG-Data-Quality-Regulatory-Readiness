"""Reproducible ESG data-quality and regulatory-readiness pipeline.

All source records are synthetic. Regulatory-readiness outputs are portfolio
control indicators only; they are not legal or compliance determinations.
"""

from pathlib import Path

import numpy as np
import pandas as pd


BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
DEFAULT_YEARS = (2024, 2025)

FLAG_DEFINITIONS = (
    ("DQ001", "Missing Value", "High", "Obtain the missing metric value.", "Missing_Value_Flag"),
    ("DQ002", "Duplicate Record", "Medium", "Remove the duplicate after source verification.", "Duplicate_Flag"),
    ("DQ003", "Invalid Unit", "Medium", "Standardize to the controlled metric unit.", "Invalid_Unit_Flag"),
    ("DQ004", "Negative Emissions", "Critical", "Verify the negative emissions value against the source.", "Negative_Emissions_Flag"),
    ("DQ005", "Missing Reporting Year", "High", "Confirm and populate the reporting period.", "Missing_Year_Flag"),
    ("DQ006", "Missing Scope", "High", "Confirm the GHG scope classification.", "Missing_Scope_Flag"),
    ("DQ008", "Outlier", "Medium", "Review the unusual value against supporting evidence.", "Outlier_Flag"),
    ("DQ009", "Missing Source", "Low", "Attach the missing source reference.", "Missing_Source_Flag"),
)

READINESS_REQUIREMENTS = {
    "Scope 1": "Scope 1 Emissions",
    "Scope 2": "Scope 2 Emissions",
    "Scope 3": "Scope 3 Emissions",
    "Energy consumption": "Energy Consumption",
    "Renewable energy": "Renewable Energy Consumption",
    "Emissions reduction target": "Emissions Reduction Target",
    "Net-zero target": "Net Zero Target",
    "Water": "Water Consumption",
    "Waste": "Waste Generated",
}


def _read_reference() -> pd.DataFrame:
    ref = pd.read_csv(DATA / "metric_reference.csv")
    required = {"Metric", "ESG_Category", "Expected_Unit", "Required_Flag"}
    missing = required.difference(ref.columns)
    if missing:
        raise ValueError(f"metric_reference.csv is missing columns: {sorted(missing)}")
    if ref["Metric"].duplicated().any():
        raise ValueError("Metric must be unique in metric_reference.csv")
    return ref


def _severity(row: pd.Series) -> str:
    if row["Negative_Emissions_Flag"]:
        return "Critical"
    if row[["Missing_Value_Flag", "Missing_Scope_Flag", "Missing_Year_Flag"]].any():
        return "High"
    if row[["Invalid_Unit_Flag", "Outlier_Flag", "Duplicate_Flag"]].any():
        return "Medium"
    if row["Missing_Source_Flag"]:
        return "Low"
    return "None"


def _score_group(group: pd.DataFrame, completeness_pct: float) -> dict:
    validity_fail = group[
        ["Missing_Value_Flag", "Invalid_Unit_Flag", "Negative_Emissions_Flag", "Missing_Year_Flag", "Missing_Scope_Flag"]
    ].any(axis=1)
    consistency_fail = group[["Duplicate_Flag", "Outlier_Flag"]].any(axis=1)
    validity = (1 - validity_fail.mean()) * 100
    consistency = (1 - consistency_fail.mean()) * 100
    traceability = (1 - group["Missing_Source_Flag"].mean()) * 100
    score = 0.30 * completeness_pct + 0.30 * validity + 0.25 * consistency + 0.15 * traceability
    return {
        "Total_Records": int(len(group)),
        "Valid_Records": int((group["Validation_Status"] == "Valid").sum()),
        "Record_Pass_Rate": round((group["Validation_Status"] == "Valid").mean() * 100, 1),
        "Completeness_Pct": round(completeness_pct, 1),
        "Validity_Pct": round(validity, 1),
        "Consistency_Pct": round(consistency, 1),
        "Traceability_Pct": round(traceability, 1),
        "Data_Quality_Score": round(score, 1),
        "Exception_Count": int(group["Exception_Count"].sum()),
        "High_Critical_Exception_Count": 0,
    }


def build_outputs(raw_path: Path = DATA / "raw_esg_data.csv"):
    ref = _read_reference()
    raw = pd.read_csv(raw_path)
    required_raw = {
        "Record_ID", "Company", "Industry", "Country", "Reporting_Year", "ESG_Category",
        "Metric", "Scope", "Value", "Unit", "Source_Type", "Source_Reference"
    }
    missing = required_raw.difference(raw.columns)
    if missing:
        raise ValueError(f"raw_esg_data.csv is missing columns: {sorted(missing)}")
    if raw["Record_ID"].duplicated().any():
        raise ValueError("Record_ID must be unique")

    r = raw.drop(columns=["Expected_Unit"], errors="ignore").merge(
        ref[["Metric", "Expected_Unit", "ESG_Category", "Required_Flag"]],
        on="Metric", how="left", suffixes=("", "_Reference"), validate="many_to_one"
    )
    r["Unique_Record_Key"] = (
        r["Company"].fillna("") + "|" + r["Reporting_Year"].fillna(-1).astype(str) + "|" + r["Metric"].fillna("")
    )
    r["Duplicate_Flag"] = r.duplicated(["Company", "Reporting_Year", "Metric"], keep=False)
    r["Missing_Value_Flag"] = r["Value"].isna()
    r["Invalid_Unit_Flag"] = r["Expected_Unit"].notna() & r["Unit"].ne(r["Expected_Unit"])
    numeric_value = pd.to_numeric(r["Value"], errors="coerce")
    emissions = r["Metric"].str.contains("Emissions", na=False)
    r["Negative_Emissions_Flag"] = emissions & numeric_value.lt(0)
    r["Missing_Scope_Flag"] = emissions & r["Scope"].isna()
    r["Missing_Year_Flag"] = r["Reporting_Year"].isna()
    r["Missing_Source_Flag"] = r["Source_Reference"].isna()
    r["Outlier_Flag"] = False
    for _, metric_group in r.groupby("Metric", dropna=False):
        values = pd.to_numeric(metric_group["Value"], errors="coerce")
        q1, q3 = values.quantile(0.25), values.quantile(0.75)
        iqr = q3 - q1
        if pd.notna(iqr) and iqr > 0:
            r.loc[metric_group.index, "Outlier_Flag"] = (values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)

    flag_columns = [definition[4] for definition in FLAG_DEFINITIONS]
    r["Exception_Count"] = r[flag_columns].sum(axis=1).astype(int)
    r["Validation_Status"] = np.where(r["Exception_Count"].eq(0), "Valid", "Exception")
    r["Severity"] = r.apply(_severity, axis=1)
    r.to_csv(DATA / "validated_esg_data.csv", index=False)

    exception_rows = []
    exception_id = 1
    for _, row in r[r["Exception_Count"].gt(0)].iterrows():
        for rule_id, issue_type, severity, action, flag in FLAG_DEFINITIONS:
            if bool(row[flag]):
                exception_rows.append({
                    "Exception_ID": f"E{exception_id:04d}", "Record_ID": row["Record_ID"],
                    "Company": row["Company"], "Industry": row["Industry"], "Country": row["Country"],
                    "Reporting_Year": row["Reporting_Year"], "ESG_Category": row["ESG_Category"],
                    "Metric": row["Metric"], "Source_Type": row["Source_Type"], "Rule_ID": rule_id,
                    "Exception_Type": issue_type, "Severity": severity,
                    "Severity_Rank": {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}[severity],
                    "Original_Value": row["Value"], "Original_Unit": row["Unit"],
                    "Description": f"{issue_type} detected by deterministic validation.",
                    "Recommended_Action": action, "Remediation_Status": "Open", "Exception_Count": 1,
                })
                exception_id += 1
    exc = pd.DataFrame(exception_rows)
    exc.to_csv(DATA / "esg_exception_log.csv", index=False)
    exc.to_csv(DATA / "tableau_issues.csv", index=False)

    companies = sorted(r["Company"].dropna().unique())
    years = sorted(set(DEFAULT_YEARS).union(r["Reporting_Year"].dropna().astype(int).unique()))
    expected_metrics = ref.loc[ref["Required_Flag"].astype(bool), "Metric"].tolist()
    entity_lookup = r.groupby("Company")[["Industry", "Country"]].first()
    completeness_rows = []
    for company in companies:
        for year in years:
            scoped = r[(r["Company"] == company) & (r["Reporting_Year"] == year)]
            for metric in expected_metrics:
                reference = ref.loc[ref["Metric"] == metric].iloc[0]
                available = int((scoped["Metric"] == metric).any())
                completeness_rows.append({
                    "Company": company, "Industry": entity_lookup.loc[company, "Industry"],
                    "Country": entity_lookup.loc[company, "Country"], "Reporting_Year": year,
                    "ESG_Category": reference["ESG_Category"], "Metric": metric,
                    "Availability_Flag": available, "Availability": "Available" if available else "Missing",
                })
    cm = pd.DataFrame(completeness_rows)
    cm.to_csv(DATA / "esg_metric_completeness.csv", index=False)
    cm.to_csv(DATA / "tableau_completeness_detail.csv", index=False)

    overview_rows = []
    for company in companies:
        for year in years:
            group = r[(r["Company"] == company) & (r["Reporting_Year"] == year)]
            completeness = cm[(cm["Company"] == company) & (cm["Reporting_Year"] == year)]["Availability_Flag"].mean() * 100
            scores = _score_group(group, completeness)
            scores.update({"Company": company, "Industry": entity_lookup.loc[company, "Industry"],
                           "Country": entity_lookup.loc[company, "Country"], "Reporting_Year": year})
            high_critical = exc[(exc["Company"] == company) & (exc["Reporting_Year"] == year) & exc["Severity"].isin(["Critical", "High"])]
            scores["High_Critical_Exception_Count"] = int(len(high_critical))
            overview_rows.append(scores)
    overview = pd.DataFrame(overview_rows)[[
        "Company", "Industry", "Country", "Reporting_Year", "Total_Records", "Valid_Records",
        "Record_Pass_Rate", "Completeness_Pct", "Validity_Pct", "Consistency_Pct",
        "Traceability_Pct", "Data_Quality_Score", "Exception_Count", "High_Critical_Exception_Count",
    ]]
    overview["Period_Date"] = pd.to_datetime(overview["Reporting_Year"].astype(str) + "-12-31")
    overview.to_csv(DATA / "tableau_overview.csv", index=False)

    year_summary_rows = []
    for year in years:
        year_records = r[r["Reporting_Year"] == year]
        year_completeness = cm.loc[cm["Reporting_Year"] == year, "Availability_Flag"].mean() * 100
        row = _score_group(year_records, year_completeness)
        row["High_Critical_Exception_Count"] = int(
            exc[(exc["Reporting_Year"] == year) & exc["Severity"].isin(["Critical", "High"])].shape[0]
        )
        row.update({"Reporting_Year": year, "Period_Date": f"{year}-12-31"})
        year_summary_rows.append(row)
    pd.DataFrame(year_summary_rows).to_csv(DATA / "tableau_year_summary.csv", index=False)

    company_quality = overview.groupby(["Company", "Industry", "Country"], as_index=False).agg(
        Total_Records=("Total_Records", "sum"), Valid_Records=("Valid_Records", "sum"),
        Record_Pass_Rate=("Record_Pass_Rate", "mean"), Completeness_Pct=("Completeness_Pct", "mean"),
        Validity_Pct=("Validity_Pct", "mean"), Consistency_Pct=("Consistency_Pct", "mean"),
        Traceability_Pct=("Traceability_Pct", "mean"), Data_Quality_Score=("Data_Quality_Score", "mean"),
        Exception_Count=("Exception_Count", "sum"), High_Critical_Exception_Count=("High_Critical_Exception_Count", "sum"),
    )
    for column in ["Record_Pass_Rate", "Completeness_Pct", "Validity_Pct", "Consistency_Pct", "Traceability_Pct", "Data_Quality_Score"]:
        company_quality[column] = company_quality[column].round(1)
    company_quality.to_csv(DATA / "esg_company_quality.csv", index=False)
    company_quality.to_csv(DATA / "tableau_company_quality.csv", index=False)

    metric_completeness = cm.groupby(["ESG_Category", "Metric"], as_index=False)["Availability_Flag"].agg(
        Expected_Company_Years="count", Available_Company_Years="sum"
    )
    metric_completeness["Completeness_Pct"] = (metric_completeness["Available_Company_Years"] / metric_completeness["Expected_Company_Years"] * 100).round(1)
    metric_completeness.to_csv(DATA / "tableau_metric_completeness.csv", index=False)
    cm[cm["Metric"].str.match(r"Scope [123] Emissions")].groupby("Metric")["Availability_Flag"].mean().mul(100).round(1).reset_index(name="Completeness_Pct").to_csv(DATA / "tableau_scope_completeness.csv", index=False)

    readiness_rows = []
    for company in companies:
        for year in years:
            quality = float(overview.loc[(overview["Company"] == company) & (overview["Reporting_Year"] == year), "Data_Quality_Score"].iloc[0])
            requirement_rows = []
            for area, metric in READINESS_REQUIREMENTS.items():
                available = int(cm.loc[(cm["Company"] == company) & (cm["Reporting_Year"] == year) & (cm["Metric"] == metric), "Availability_Flag"].iloc[0])
                requirement_rows.append((area, metric, available))
            coverage = np.mean([row[2] for row in requirement_rows]) * 100
            readiness_score = round(0.70 * coverage + 0.30 * quality, 1)
            high_risk_gaps = sum(1 for area, _, available in requirement_rows if not available and area in {"Scope 1", "Scope 2", "Scope 3"})
            for area, metric, available in requirement_rows:
                gap = not bool(available)
                priority = "Critical" if gap and area in {"Scope 1", "Scope 2", "Scope 3"} else ("High" if gap else "Low")
                readiness_rows.append({
                    "Company": company, "Industry": entity_lookup.loc[company, "Industry"],
                    "Country": entity_lookup.loc[company, "Country"], "Reporting_Year": year,
                    "Requirement_Area": area, "Required_Data": metric,
                    "Availability": "Available" if available else "Missing", "Availability_Flag": available,
                    "Requirement_Count": 1, "Gap_Flag": int(gap),
                    "Regulatory_Coverage_Pct": round(coverage, 1), "Data_Quality_Score": quality,
                    "Readiness_Score": readiness_score, "Gap": "Gap identified" if gap else "No gap",
                    "Priority": priority, "High_Risk_Gap_Count": high_risk_gaps,
                    "Recommended_Action": "Close the data gap and validate supporting evidence." if gap else "Maintain evidence and scheduled validation.",
                })
    readiness = pd.DataFrame(readiness_rows)
    readiness.to_csv(DATA / "reporting_readiness.csv", index=False)
    readiness.to_csv(DATA / "tableau_readiness.csv", index=False)
    readiness_summary = readiness.groupby(
        ["Company", "Industry", "Country", "Reporting_Year"], as_index=False
    ).agg(
        Readiness_Score=("Readiness_Score", "first"),
        Regulatory_Coverage_Pct=("Regulatory_Coverage_Pct", "first"),
        Data_Quality_Score=("Data_Quality_Score", "first"),
        Outstanding_Requirements=("Availability_Flag", lambda values: int((values == 0).sum())),
        High_Risk_Gap_Count=("High_Risk_Gap_Count", "first"),
    )
    readiness_summary["Period_Date"] = pd.to_datetime(readiness_summary["Reporting_Year"].astype(str) + "-12-31")
    readiness_summary.to_csv(DATA / "tableau_readiness_summary.csv", index=False)
    readiness_company = readiness_summary.groupby(["Company", "Industry", "Country"], as_index=False).agg(
        Readiness_Score=("Readiness_Score", "mean"),
        Regulatory_Coverage_Pct=("Regulatory_Coverage_Pct", "mean"),
        Data_Quality_Score=("Data_Quality_Score", "mean"),
        Outstanding_Requirements=("Outstanding_Requirements", "sum"),
        High_Risk_Gap_Count=("High_Risk_Gap_Count", "sum"),
    )
    for column in ["Readiness_Score", "Regulatory_Coverage_Pct", "Data_Quality_Score"]:
        readiness_company[column] = readiness_company[column].round(1)
    readiness_company.to_csv(DATA / "tableau_readiness_company.csv", index=False)

    overall_completeness = cm["Availability_Flag"].mean() * 100
    overall_scores = _score_group(r, overall_completeness)
    overall_scores["High_Critical_Exception_Count"] = int(exc["Severity"].isin(["Critical", "High"]).sum())
    pd.DataFrame([{"Scope": "Overall", **overall_scores}]).to_csv(DATA / "esg_quality_summary.csv", index=False)
    exc.groupby(["Exception_Type", "Severity"], as_index=False)["Exception_Count"].sum().to_csv(DATA / "tableau_exception_summary.csv", index=False)
    return r, exc, company_quality, cm


if __name__ == "__main__":
    build_outputs()
