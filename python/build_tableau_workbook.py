"""Build the portfolio Tableau workbook from validated CSV outputs.

The script uses the bundled executable Tableau chart catalog for worksheet
generation, then assembles four fixed-size dashboards and a portable package.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd

from esg_data_quality_engine import build_outputs


BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
TABLEAU = BASE / "tableau"
PACKAGE_DATA = TABLEAU / "Data"
PLUGIN = Path.home() / ".codex/plugins/cache/openai-curated-remote/Tableau/2.0.0/skills/tableau-workbook-authoring"
CATALOG = PLUGIN / "scripts/tableau_resources.py"

CSV_SOURCES = {
    "summary": "esg_quality_summary.csv",
    "year": "tableau_year_summary.csv",
    "company": "tableau_company_quality.csv",
    "issues": "tableau_issues.csv",
    "completeness": "tableau_metric_completeness.csv",
    "scope": "tableau_scope_completeness.csv",
    "readiness_company": "tableau_readiness_company.csv",
    "readiness": "tableau_readiness.csv",
}

CHARTS = {
    "summary": [
        ("kpi-text", "KPI | Data Quality Score", {"Profit": "Data_Quality_Score"}),
        ("kpi-text", "KPI | Completeness", {"Profit": "Completeness_Pct"}),
        ("kpi-text", "KPI | Validity", {"Profit": "Validity_Pct"}),
        ("kpi-text", "KPI | Consistency", {"Profit": "Consistency_Pct"}),
        ("kpi-text", "KPI | Traceability", {"Profit": "Traceability_Pct"}),
        ("kpi-text", "KPI | Records Assessed", {"Profit": "Total_Records"}),
        ("kpi-text", "KPI | Exceptions", {"Profit": "Exception_Count"}),
        ("kpi-text", "KPI | High + Critical", {"Profit": "High_Critical_Exception_Count"}),
    ],
    "year": [
        ("insights__line_chart", "Trend | Data Quality", {"ARR": "Data_Quality_Score", "Close Date": "Period_Date"}),
        ("insights__line_chart", "Trend | Record Pass Rate", {"ARR": "Record_Pass_Rate", "Close Date": "Period_Date"}),
    ],
    "company": [
        ("ranking-ordered-bar", "Company | Data Quality", {"Customer Name": "Company", "Profit": "Data_Quality_Score"}),
        ("ranking-ordered-bar", "Company | Completeness", {"Customer Name": "Company", "Profit": "Completeness_Pct"}),
    ],
    "issues": [
        ("ranking-ordered-bar", "Issues | Exception Type", {"Customer Name": "Exception_Type", "Profit": "Exception_Count"}),
        ("ranking-ordered-bar", "Issues | Priority Company", {"Customer Name": "Company", "Profit": "Exception_Count"}),
        ("part-to-whole-stacked-bar-chart", "Issues | Severity by Company", {"Customer Name": "Company", "Product Name": "Severity", "Profit": "Exception_Count"}),
    ],
    "completeness": [
        ("ranking-ordered-bar", "Coverage | Metric", {"Customer Name": "Metric", "Profit": "Completeness_Pct"}),
    ],
    "scope": [
        ("magnitude-simple-bar", "Coverage | Scope 1 2 3", {"Customer Name": "Metric", "Profit": "Completeness_Pct"}),
    ],
    "readiness_company": [
        ("ranking-ordered-bar", "Readiness | Company", {"Customer Name": "Company", "Profit": "Readiness_Score"}),
        ("ranking-ordered-bar", "Readiness | Outstanding Requirements", {"Customer Name": "Company", "Profit": "Outstanding_Requirements"}),
        ("ranking-ordered-bar", "Readiness | High Risk Gaps", {"Customer Name": "Company", "Profit": "High_Risk_Gap_Count"}),
    ],
    "readiness": [
        ("part-to-whole-stacked-bar-chart", "Readiness | Requirement Status", {"Customer Name": "Requirement_Area", "Product Name": "Availability", "Profit": "Requirement_Count"}),
    ],
}


def tableau_type(series: pd.Series, field: str) -> tuple[str, str, str]:
    if field.endswith("_Date"):
        return "date", "dimension", "ordinal"
    if pd.api.types.is_bool_dtype(series):
        return "boolean", "dimension", "nominal"
    if pd.api.types.is_integer_dtype(series):
        return "integer", "measure", "quantitative"
    if pd.api.types.is_numeric_dtype(series):
        return "real", "measure", "quantitative"
    return "string", "dimension", "nominal"


def datasource_definition(key: str, csv_name: str, destination: Path) -> str:
    frame = pd.read_csv(DATA / csv_name)
    name = f"ds.{key}"
    root = ET.Element("datasource", {"caption": key.replace("_", " ").title(), "inline": "true", "name": name, "version": "18.1"})
    ET.SubElement(root, "connection", {
        "class": "textscan", "directory": "Data", "filename": csv_name,
        "server": "", "workgroup-auth-mode": "as-is",
    })
    ET.SubElement(root, "aliases", {"enabled": "yes"})
    for field in frame.columns:
        dtype, role, kind = tableau_type(frame[field], field)
        ET.SubElement(root, "column", {"datatype": dtype, "name": f"[{field}]", "role": role, "type": kind})
    ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)
    return name


def run_catalog(args: list[str]) -> None:
    completed = subprocess.run([sys.executable, str(CATALOG), *args], cwd=BASE, text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError(f"Tableau catalog command failed:\n{completed.stdout}\n{completed.stderr}")


def build_group(temp: Path, key: str) -> Path:
    ds_file = temp / f"{key}-datasource.xml"
    ds_name = datasource_definition(key, CSV_SOURCES[key], ds_file)
    output = temp / f"{key}.twb"
    for index, (resource, sheet_name, mappings) in enumerate(CHARTS[key]):
        mapping_args = [item for source, target in mappings.items() for item in ("--map", f"{source}={target}")]
        if index == 0:
            run_catalog(["instantiate", resource, "--datasource-definition", str(ds_file), "--output", str(output),
                         "--worksheet-name", sheet_name, *mapping_args])
        else:
            run_catalog(["inject", resource, "--input", str(output), "--output", str(output), "--overwrite",
                         "--datasource", ds_name, "--worksheet-name", sheet_name, *mapping_args])
    return output


def improve_sheet_format(worksheet: ET.Element) -> None:
    name = worksheet.attrib["name"]
    table = worksheet.find("table")
    if table is None:
        return
    style = table.find("style")
    if style is None:
        style = ET.SubElement(table, "style")
    rule = ET.SubElement(style, "style-rule", {"element": "worksheet"})
    ET.SubElement(rule, "format", {"attr": "background-color", "value": "#FFFFFF"})
    ET.SubElement(rule, "format", {"attr": "font-face", "value": "Tableau Book"})
    if name.startswith("KPI"):
        panes = table.find("panes")
        if panes is not None:
            mark_rule = ET.SubElement(panes.find("pane"), "style")
            sr = ET.SubElement(mark_rule, "style-rule", {"element": "mark"})
            ET.SubElement(sr, "format", {"attr": "font-size", "value": "22"})
            ET.SubElement(sr, "format", {"attr": "font-weight", "value": "bold"})
            ET.SubElement(sr, "format", {"attr": "color", "value": "#17324D"})


def add_dashboard(root: ET.Element, name: str, placements: list[tuple[str, int, int, int, int]], zone_start: int) -> tuple[ET.Element, int]:
    dashboard = ET.Element("dashboard", {"name": name})
    ET.SubElement(dashboard, "size", {"sizing-mode": "fixed", "minwidth": "1200", "maxwidth": "1200", "minheight": "800", "maxheight": "800"})
    zones = ET.SubElement(dashboard, "zones")
    outer = ET.SubElement(zones, "zone", {"id": str(zone_start), "x": "0", "y": "0", "w": "1200", "h": "800", "type-v2": "layout-basic", "layout-strategy-id": "basic"})
    zone_start += 1
    ET.SubElement(outer, "zone", {"id": str(zone_start), "x": "0", "y": "0", "w": "1200", "h": "48", "type-v2": "title"})
    zone_start += 1
    for sheet, x, y, w, h in placements:
        zone = ET.SubElement(outer, "zone", {"id": str(zone_start), "x": str(x), "y": str(y), "w": str(w), "h": str(h), "type-v2": "visual", "name": sheet})
        zone_style = ET.SubElement(zone, "zone-style")
        ET.SubElement(zone_style, "format", {"attr": "border-color", "value": "#DCE3EA"})
        ET.SubElement(zone_style, "format", {"attr": "border-style", "value": "solid"})
        ET.SubElement(zone_style, "format", {"attr": "border-width", "value": "1"})
        ET.SubElement(zone_style, "format", {"attr": "margin", "value": "6"})
        zone_start += 1
    return dashboard, zone_start


def assemble(groups: list[Path], output: Path) -> None:
    root = ET.Element("workbook", {"original-version": "18.1", "source-build": "portfolio", "source-platform": "win", "version": "18.1", "xmlns:user": "http://www.tableausoftware.com/xml/user"})
    manifest = ET.SubElement(root, "document-format-change-manifest")
    ET.SubElement(manifest, "WindowsPersistSimpleIdentifiers")
    ET.SubElement(root, "preferences")
    datasources = ET.SubElement(root, "datasources")
    worksheets = ET.SubElement(root, "worksheets")
    worksheet_windows = []
    for group in groups:
        source_root = ET.parse(group).getroot()
        for ds in source_root.find("datasources"):
            datasources.append(ds)
        for worksheet in source_root.find("worksheets"):
            improve_sheet_format(worksheet)
            worksheets.append(worksheet)
        for window in source_root.find("windows"):
            worksheet_windows.append(window)

    dashboard_container = ET.SubElement(root, "dashboards")
    dashboard_specs = [
        ("01 | Executive Data Quality Overview", [
            ("KPI | Data Quality Score", 0, 48, 200, 130), ("KPI | Completeness", 200, 48, 200, 130),
            ("KPI | Validity", 400, 48, 200, 130), ("KPI | Consistency", 600, 48, 200, 130),
            ("KPI | Traceability", 800, 48, 200, 130), ("KPI | Records Assessed", 1000, 48, 200, 130),
            ("Trend | Data Quality", 0, 178, 560, 300), ("Company | Data Quality", 560, 178, 640, 300),
            ("KPI | Exceptions", 0, 478, 300, 322), ("KPI | High + Critical", 300, 478, 300, 322),
            ("Trend | Record Pass Rate", 600, 478, 600, 322),
        ]),
        ("02 | Data Quality Analysis", [
            ("Company | Data Quality", 0, 48, 600, 350), ("Issues | Exception Type", 600, 48, 600, 350),
            ("Coverage | Metric", 0, 398, 800, 402), ("Coverage | Scope 1 2 3", 800, 398, 400, 402),
        ]),
        ("03 | Regulatory Readiness", [
            ("Readiness | Company", 0, 48, 600, 360), ("Readiness | Requirement Status", 600, 48, 600, 360),
            ("Readiness | Outstanding Requirements", 0, 408, 600, 392), ("Readiness | High Risk Gaps", 600, 408, 600, 392),
        ]),
        ("04 | Exceptions and Remediation", [
            ("KPI | Exceptions", 0, 48, 300, 160), ("KPI | High + Critical", 300, 48, 300, 160),
            ("Issues | Exception Type", 600, 48, 600, 320), ("Issues | Severity by Company", 0, 208, 600, 592),
            ("Issues | Priority Company", 600, 368, 600, 432),
        ]),
    ]
    dashboard_windows = []
    zone_id = 2
    for dashboard_name, placements in dashboard_specs:
        dashboard, zone_id = add_dashboard(root, dashboard_name, placements, zone_id)
        dashboard_container.append(dashboard)
        window = ET.Element("window", {"class": "dashboard", "maximized": "true", "name": dashboard_name})
        viewpoints = ET.SubElement(window, "viewpoints")
        for sheet, *_ in placements:
            ET.SubElement(viewpoints, "viewpoint", {"name": sheet})
        ET.SubElement(window, "active", {"id": "-1"})
        dashboard_windows.append(window)

    windows = ET.SubElement(root, "windows")
    for window in worksheet_windows + dashboard_windows:
        windows.append(window)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)


def package_workbook(twb: Path, twbx: Path) -> None:
    with zipfile.ZipFile(twbx, "w", compression=zipfile.ZIP_DEFLATED) as package:
        package.write(twb, twb.name)
        for csv_name in CSV_SOURCES.values():
            package.write(PACKAGE_DATA / csv_name, f"Data/{csv_name}")


def main() -> None:
    build_outputs()
    TABLEAU.mkdir(exist_ok=True)
    PACKAGE_DATA.mkdir(exist_ok=True)
    for csv_name in sorted(set(CSV_SOURCES.values())):
        shutil.copy2(DATA / csv_name, PACKAGE_DATA / csv_name)
    with tempfile.TemporaryDirectory(prefix="esg-tableau-") as temp_name:
        temp = Path(temp_name)
        groups = [build_group(temp, key) for key in CHARTS]
        twb = TABLEAU / "ESG_Data_Quality_Regulatory_Readiness.twb"
        assemble(groups, twb)
    run_catalog(["validate", "--input", str(twb)])
    package_workbook(twb, TABLEAU / "ESG_Data_Quality_Regulatory_Readiness.twbx")
    print(f"Built {twb}")


if __name__ == "__main__":
    main()
