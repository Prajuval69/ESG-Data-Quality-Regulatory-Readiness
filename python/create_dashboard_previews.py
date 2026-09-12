"""Create static portfolio previews from the same CSVs used by Tableau."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
OUTPUT = BASE / "docs" / "images"
OUTPUT.mkdir(parents=True, exist_ok=True)

NAVY, BLUE, TEAL, AMBER, RED = "#17324D", "#2F6690", "#2A9D8F", "#E9C46A", "#D1495B"
BG, GRID, TEXT, MUTED = "#F4F7FA", "#DCE3EA", "#243447", "#64748B"


def base_figure(title: str, subtitle: str):
    fig = plt.figure(figsize=(16, 9), facecolor=BG)
    fig.text(0.035, 0.955, title, fontsize=23, fontweight="bold", color=NAVY, va="top")
    fig.text(0.035, 0.915, subtitle, fontsize=10.5, color=MUTED, va="top")
    return fig


def card(fig, x, y, w, h, label, value, accent=BLUE):
    ax = fig.add_axes([x, y, w, h], facecolor="white")
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.axvspan(0, 0.025, color=accent)
    ax.text(0.08, 0.68, label.upper(), fontsize=9, color=MUTED, transform=ax.transAxes, fontweight="bold")
    ax.text(0.08, 0.22, value, fontsize=23, color=NAVY, transform=ax.transAxes, fontweight="bold")
    return ax


def clean(ax, title):
    ax.set_facecolor("white")
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", color=NAVY, pad=12)
    ax.grid(axis="x", color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8.5)


def save(fig, filename):
    fig.text(0.035, 0.018, "Synthetic portfolio data • Readiness indicators are not legal compliance determinations", fontsize=8.5, color=MUTED)
    fig.savefig(OUTPUT / filename, dpi=160, bbox_inches="tight", facecolor=BG)
    plt.close(fig)


summary = pd.read_csv(DATA / "esg_quality_summary.csv").iloc[0]
year = pd.read_csv(DATA / "tableau_year_summary.csv")
company = pd.read_csv(DATA / "tableau_company_quality.csv").sort_values("Data_Quality_Score")
issues = pd.read_csv(DATA / "tableau_issues.csv")
metric = pd.read_csv(DATA / "tableau_metric_completeness.csv").sort_values("Completeness_Pct")
scope = pd.read_csv(DATA / "tableau_scope_completeness.csv").sort_values("Metric")
readiness = pd.read_csv(DATA / "tableau_readiness.csv")
readiness_company = pd.read_csv(DATA / "tableau_readiness_company.csv").sort_values("Readiness_Score")

# Executive overview
fig = base_figure("Executive Data Quality Overview", "How healthy is the synthetic ESG reporting dataset?")
card(fig, .035, .74, .175, .13, "Data quality score", f"{summary.Data_Quality_Score:.1f}%", TEAL)
card(fig, .22, .74, .14, .13, "Completeness", f"{summary.Completeness_Pct:.1f}%", AMBER)
card(fig, .37, .74, .14, .13, "Validity", f"{summary.Validity_Pct:.1f}%", TEAL)
card(fig, .52, .74, .14, .13, "Consistency", f"{summary.Consistency_Pct:.1f}%", BLUE)
card(fig, .67, .74, .14, .13, "Traceability", f"{summary.Traceability_Pct:.1f}%", TEAL)
card(fig, .82, .74, .145, .13, "Exceptions", f"{int(summary.Exception_Count)}", RED)
ax = fig.add_axes([.035, .10, .40, .56]); clean(ax, "Portfolio score trend")
ax.plot(year.Reporting_Year, year.Data_Quality_Score, color=BLUE, marker="o", linewidth=3, markersize=8)
ax.fill_between(year.Reporting_Year, year.Data_Quality_Score, alpha=.12, color=BLUE)
ax.set_ylim(80, 95); ax.set_xticks(year.Reporting_Year); ax.set_ylabel("Score (%)", color=MUTED)
for x, y in zip(year.Reporting_Year, year.Data_Quality_Score): ax.text(x, y+.7, f"{y:.1f}%", ha="center", color=NAVY, fontweight="bold")
ax = fig.add_axes([.48, .10, .485, .56]); clean(ax, "Company data-quality score")
colors = [RED if v < 85 else AMBER if v < 90 else TEAL for v in company.Data_Quality_Score]
ax.barh(company.Company, company.Data_Quality_Score, color=colors)
ax.set_xlim(75, 100); ax.set_xlabel("Portfolio-defined score (%)", color=MUTED)
save(fig, "tableau_01_executive_overview.png")

# Data quality analysis
fig = base_figure("Data Quality Analysis", "Where are the largest quality and coverage weaknesses?")
ax = fig.add_axes([.035, .52, .44, .34]); clean(ax, "Exceptions by rule")
issue_counts = issues.groupby("Exception_Type").Exception_Count.sum().sort_values()
ax.barh(issue_counts.index, issue_counts.values, color=[RED if "Negative" in i else BLUE for i in issue_counts.index])
ax.set_xlabel("Exception instances", color=MUTED)
ax = fig.add_axes([.52, .52, .445, .34]); clean(ax, "Company record pass rate")
ordered = company.sort_values("Record_Pass_Rate")
ax.barh(ordered.Company, ordered.Record_Pass_Rate, color=BLUE); ax.set_xlim(45, 100); ax.set_xlabel("Records with no automated exception (%)", color=MUTED)
ax = fig.add_axes([.035, .10, .60, .34]); clean(ax, "Required metric completeness")
ax.barh(metric.Metric, metric.Completeness_Pct, color=[RED if v < 65 else AMBER if v < 80 else TEAL for v in metric.Completeness_Pct])
ax.set_xlim(50, 100); ax.set_xlabel("Expected company-years available (%)", color=MUTED)
ax = fig.add_axes([.68, .10, .285, .34]); clean(ax, "GHG scope completeness")
ax.bar(scope.Metric.str.replace(" Emissions", "", regex=False), scope.Completeness_Pct, color=[TEAL, BLUE, AMBER])
ax.set_ylim(0, 100); ax.set_ylabel("Completeness (%)", color=MUTED); ax.grid(axis="y", color=GRID)
save(fig, "tableau_02_data_quality_analysis.png")

# Regulatory readiness
fig = base_figure("Regulatory Readiness", "Portfolio readiness screening: data coverage plus data quality, not a compliance opinion")
card(fig, .035, .74, .21, .13, "Average readiness", f"{readiness_company.Readiness_Score.mean():.1f}%", BLUE)
card(fig, .26, .74, .21, .13, "Regulatory coverage", f"{readiness_company.Regulatory_Coverage_Pct.mean():.1f}%", AMBER)
card(fig, .485, .74, .21, .13, "Outstanding requirements", f"{int(readiness_company.Outstanding_Requirements.sum())}", RED)
card(fig, .71, .74, .255, .13, "High-risk GHG gaps", f"{int(readiness_company.High_Risk_Gap_Count.sum())}", RED)
ax = fig.add_axes([.035, .10, .43, .56]); clean(ax, "Readiness score by company")
ax.barh(readiness_company.Company, readiness_company.Readiness_Score, color=[RED if v < 70 else AMBER if v < 80 else TEAL for v in readiness_company.Readiness_Score])
ax.set_xlim(55, 100); ax.set_xlabel("Readiness score (%)", color=MUTED)
ax = fig.add_axes([.51, .36, .455, .30]); clean(ax, "Requirement coverage")
coverage = readiness.groupby("Requirement_Area").Availability_Flag.mean().mul(100).sort_values()
ax.barh(coverage.index, coverage.values, color=[RED if v < 65 else AMBER if v < 80 else TEAL for v in coverage.values]); ax.set_xlim(45, 100)
ax.set_xlabel("Company-years available (%)", color=MUTED)
ax = fig.add_axes([.51, .10, .455, .18]); clean(ax, "Outstanding requirements by company")
gaps = readiness_company.sort_values("Outstanding_Requirements", ascending=False).head(8)
ax.bar(gaps.Company, gaps.Outstanding_Requirements, color=RED); ax.tick_params(axis="x", rotation=28); ax.set_ylabel("Gaps", color=MUTED)
save(fig, "tableau_03_regulatory_readiness.png")

# Exceptions and remediation
fig = base_figure("Exceptions & Remediation", "What needs to be fixed first?")
card(fig, .035, .74, .20, .13, "Open exceptions", f"{len(issues)}", RED)
card(fig, .25, .74, .20, .13, "Critical", f"{(issues.Severity == 'Critical').sum()}", RED)
card(fig, .465, .74, .20, .13, "High", f"{(issues.Severity == 'High').sum()}", AMBER)
card(fig, .68, .74, .285, .13, "Affected companies", f"{issues.Company.nunique()} of {company.Company.nunique()}", BLUE)
ax = fig.add_axes([.035, .40, .40, .27]); clean(ax, "Severity mix")
severity = issues.groupby("Severity").Exception_Count.sum().reindex(["Critical", "High", "Medium", "Low"]).fillna(0)
ax.bar(severity.index, severity.values, color=[RED, AMBER, BLUE, TEAL]); ax.set_ylabel("Exception instances", color=MUTED); ax.grid(axis="y", color=GRID)
ax = fig.add_axes([.48, .40, .485, .27]); clean(ax, "Issue burden by company")
company_issues = issues.groupby("Company").Exception_Count.sum().sort_values(ascending=False).head(8)
ax.bar(company_issues.index, company_issues.values, color=BLUE); ax.tick_params(axis="x", rotation=28); ax.set_ylabel("Exceptions", color=MUTED)
ax = fig.add_axes([.035, .09, .93, .23], facecolor="white"); ax.axis("off")
queue = issues.sort_values(["Severity_Rank", "Company"], ascending=[False, True]).head(7)
table = ax.table(cellText=queue[["Severity", "Company", "Metric", "Exception_Type", "Recommended_Action"]].values,
                 colLabels=["Severity", "Company", "Metric", "Issue", "Recommended action"],
                 cellLoc="left", colLoc="left", loc="center", colWidths=[.09, .18, .20, .17, .36])
table.auto_set_font_size(False); table.set_fontsize(7.6); table.scale(1, 1.45)
for (row_idx, _), cell in table.get_celld().items():
    cell.set_edgecolor(GRID); cell.set_linewidth(.5)
    cell.set_facecolor(NAVY if row_idx == 0 else "white")
    cell.set_text_props(color="white" if row_idx == 0 else TEXT, weight="bold" if row_idx == 0 else "normal")
save(fig, "tableau_04_exceptions_remediation.png")

print(f"Created dashboard previews in {OUTPUT}")
