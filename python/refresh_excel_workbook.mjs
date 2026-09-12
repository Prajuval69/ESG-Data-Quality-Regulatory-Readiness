import fs from "node:fs/promises";
import { pathToFileURL } from "node:url";

const artifactPath = "C:/Users/praju/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";
const { SpreadsheetFile, Workbook } = await import(pathToFileURL(artifactPath).href);

const base = "C:/Users/praju/OneDrive/Desktop/projects/ESG Data quality/ESG_Data_Quality_Regulatory_Readiness";
const outputPath = `${base}/excel/ESG_Data_Quality_Engine.xlsx`;
const navy = "#17324D", blue = "#2F6690", teal = "#2A9D8F", amber = "#E9C46A", red = "#D1495B";
const light = "#F4F7FA", border = "#DCE3EA", text = "#243447", muted = "#64748B";

function parseCsv(source) {
  const rows = []; let row = [], field = "", quoted = false;
  for (let i = 0; i < source.length; i++) {
    const ch = source[i], next = source[i + 1];
    if (quoted && ch === '"' && next === '"') { field += '"'; i++; }
    else if (ch === '"') quoted = !quoted;
    else if (!quoted && ch === ',') { row.push(field); field = ""; }
    else if (!quoted && (ch === '\n' || ch === '\r')) {
      if (ch === '\r' && next === '\n') i++;
      row.push(field); if (row.some(v => v !== "")) rows.push(row); row = []; field = "";
    } else field += ch;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows.map((values, r) => values.map(value => {
    if (r === 0 || value === "") return value === "" ? null : value;
    if (/^(true|false)$/i.test(value)) return value.toLowerCase() === "true";
    if (/^-?\d+(\.\d+)?$/.test(value)) return Number(value);
    return value;
  }));
}

async function csv(name) {
  return parseCsv(await fs.readFile(`${base}/data/${name}`, "utf8"));
}

function columnName(index) {
  let value = index + 1, result = "";
  while (value) { value--; result = String.fromCharCode(65 + value % 26) + result; value = Math.floor(value / 26); }
  return result;
}

function styleDataSheet(sheet, rows, freezeRows = 1) {
  sheet.showGridLines = false;
  const lastCol = columnName(rows[0].length - 1), lastRow = rows.length;
  const used = sheet.getRange(`A1:${lastCol}${lastRow}`);
  used.format.font = { name: "Arial", size: 9, color: text };
  used.format.verticalAlignment = "center";
  sheet.getRange(`A1:${lastCol}1`).format = {
    fill: navy, font: { name: "Arial", size: 9, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center", verticalAlignment: "center",
    borders: { preset: "inside", style: "thin", color: "#FFFFFF" },
  };
  sheet.getRange(`A1:${lastCol}1`).format.rowHeight = 28;
  used.format.autofitColumns();
  used.format.autofitRows();
  for (let c = 0; c < rows[0].length; c++) {
    const header = String(rows[0][c]);
    const col = sheet.getRange(`${columnName(c)}2:${columnName(c)}${lastRow}`);
    if (header.includes("Pct") || header.includes("Score") || header.includes("Rate")) col.format.numberFormat = "0.0";
    if (header.includes("Year")) col.format.numberFormat = "0";
  }
  sheet.freezePanes.freezeRows(freezeRows);
  sheet.tables.add(`A1:${lastCol}${lastRow}`, true, `${sheet.name.replace(/[^A-Za-z0-9]/g, "")}Table`).style = "TableStyleMedium2";
}

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Executive Summary");
const company = workbook.worksheets.add("Company Quality");
const issues = workbook.worksheets.add("Exception Log");
const completeness = workbook.worksheets.add("Metric Completeness");
const readiness = workbook.worksheets.add("Reporting Readiness");
const validated = workbook.worksheets.add("Validated Data");
const raw = workbook.worksheets.add("Raw ESG Data");
const rules = workbook.worksheets.add("Validation Rules");
const reference = workbook.worksheets.add("Metric Reference");
const dashData = workbook.worksheets.add("Dashboard Data");
const readme = workbook.worksheets.add("Read Me");

const datasets = {
  company: await csv("tableau_company_quality.csv"),
  issues: await csv("tableau_issues.csv"),
  completeness: await csv("tableau_completeness_detail.csv"),
  readiness: await csv("tableau_readiness.csv"),
  validated: await csv("validated_esg_data.csv"),
  raw: await csv("raw_esg_data.csv"),
  rules: await csv("validation_rules.csv"),
  reference: await csv("metric_reference.csv"),
  dashData: await csv("esg_quality_summary.csv"),
};

for (const [key, sheet] of Object.entries({ company, issues, completeness, readiness, validated, raw, rules, reference, dashData })) {
  const rows = datasets[key];
  sheet.getRange("A1").write(rows);
  styleDataSheet(sheet, rows);
}

summary.showGridLines = false;
summary.tabColor = navy;
summary.getRange("A1:N34").format.fill = light;
summary.getRange("B2:N2").merge();
summary.getRange("B2").values = [["ESG Data Quality & Regulatory Readiness"]];
summary.getRange("B2").format.font = { name: "Arial", size: 16, bold: true, color: navy };
summary.getRange("B3:N3").merge();
summary.getRange("B3").values = [["Synthetic portfolio | management readiness indicators, not legal compliance conclusions"]];
summary.getRange("B3").format.font = { name: "Arial", size: 9, italic: true, color: muted };

const cards = [
  ["B5:D6", "B7:D8", "DATA QUALITY SCORE", "='Dashboard Data'!I2", teal, "0.0\"%\""],
  ["E5:G6", "E7:G8", "COMPLETENESS", "='Dashboard Data'!E2", amber, "0.0\"%\""],
  ["H5:J6", "H7:J8", "VALIDITY", "='Dashboard Data'!F2", teal, "0.0\"%\""],
  ["K5:M6", "K7:M8", "EXCEPTIONS", "='Dashboard Data'!J2", red, "0"],
];
for (const [labelRange, valueRange, label, formula, color, format] of cards) {
  const labelBox = summary.getRange(labelRange); const valueBox = summary.getRange(valueRange);
  labelBox.merge(); valueBox.merge(); labelBox.format.fill = "#FFFFFF"; valueBox.format.fill = "#FFFFFF";
  labelBox.format.borders = { top: { style: "thin", color: border }, left: { style: "thin", color: border }, right: { style: "thin", color: border } };
  valueBox.format.borders = { bottom: { style: "thin", color: border }, left: { style: "thin", color: border }, right: { style: "thin", color: border } };
  const labelCell = labelRange.split(":")[0], valueCell = valueRange.split(":")[0];
  summary.getRange(labelCell).values = [[label]];
  summary.getRange(labelCell).format.font = { name: "Arial", size: 9, bold: true, color };
  summary.getRange(valueCell).formulas = [[formula]];
  summary.getRange(valueCell).format.font = { name: "Arial", size: 16, bold: true, color: navy };
  summary.getRange(valueCell).format.numberFormat = format;
}

summary.getRange("B11:F11").values = [["Company", "Quality Score", "Record Pass Rate", "Completeness", "Exceptions"]];
const companyRows = datasets.company.slice(1).sort((a, b) => b[10] - a[10]);
summary.getRange("B12").write(companyRows.map(row => [row[0], row[10], row[5], row[6], row[11]]));
summary.getRange("B11:F23").format.font = { name: "Arial", size: 9, color: text };
summary.getRange("B11:F11").format = { fill: navy, font: { name: "Arial", size: 9, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
summary.getRange("C12:E23").format.numberFormat = "0.0";
summary.getRange("B11:F23").format.borders = { preset: "inside", style: "thin", color: border };
summary.getRange("B10:F10").merge(); summary.getRange("B10").values = [["Company control performance"]];
summary.getRange("B10").format.font = { name: "Arial", size: 12, bold: true, color: navy };

const chart = summary.charts.add("bar", [summary.getRange("B11:B23"), summary.getRange("C11:C23")]);
chart.title = "Data-quality score by company"; chart.hasLegend = false;
chart.titleTextStyle.typeface = "Arial"; chart.titleTextStyle.fontSize = 12;
chart.xAxis = { axisType: "textAxis", textStyle: { typeface: "Arial", fontSize: 9 } };
chart.yAxis = { numberFormatCode: "0.0", numberFormatSourceLinked: false, textStyle: { typeface: "Arial", fontSize: 9 } };
chart.series.items[0].fill = blue; chart.setPosition("H10", "N25");

summary.getRange("B27:N31").merge();
summary.getRange("B27").values = [["Interpretation: the weighted score and record pass rate are separate measures. Completeness uses expected company-year-metric combinations. Outliers require evidence review; readiness screening is not a legal compliance opinion."]];
summary.getRange("B27").format = { fill: "#FFFFFF", font: { name: "Arial", size: 10, color: text }, wrapText: true, verticalAlignment: "center", borders: { preset: "outside", style: "thin", color: border } };
summary.getRange("A1:N34").format.rowHeight = 20;
summary.getRange("B:N").format.columnWidth = 12;

readme.showGridLines = false; readme.tabColor = "#7B8794";
readme.getRange("B2:H2").merge(); readme.getRange("B2").values = [["Workbook guide"]];
readme.getRange("B2").format.font = { name: "Arial", size: 16, bold: true, color: navy };
readme.getRange("B4:C12").values = [
  ["Purpose", "Portfolio demonstration of ESG validation, quality scoring, readiness screening, and remediation prioritization."],
  ["Data", "All companies and records are synthetic."],
  ["Score", "30% completeness + 30% validity + 25% consistency + 15% traceability."],
  ["Readiness", "70% selected requirement coverage + 30% data-quality score; not a legal conclusion."],
  ["Outliers", "1.5×IQR within metric; review signal, not automatic error."],
  ["Missing years", "Included in overall controls; excluded from year-specific analysis."],
  ["Refresh", "Run python/esg_data_quality_engine.py before refreshing downstream assets."],
  ["Primary BI", "Open tableau/ESG_Data_Quality_Regulatory_Readiness.twbx for the four-dashboard Tableau experience."],
  ["Limitation", "No source freshness dates, so timeliness and exception aging are not fabricated."],
];
readme.getRange("B4:B12").format = { fill: navy, font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" } };
readme.getRange("C4:C12").format = { fill: "#FFFFFF", font: { name: "Arial", size: 10, color: text }, wrapText: true };
readme.getRange("B4:C12").format.borders = { preset: "all", style: "thin", color: border };
readme.getRange("B:C").format.columnWidth = 25; readme.getRange("C:C").format.columnWidth = 78;
readme.getRange("B4:C12").format.rowHeight = 34;

workbook.recalculate();
const check = await workbook.inspect({ kind: "table", range: "Executive Summary!B2:N31", include: "values,formulas", tableMaxRows: 31, tableMaxCols: 13, maxChars: 5000 });
console.log(check.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "final formula error scan" });
console.log(errors.ndjson);
const preview = await workbook.render({ sheetName: "Executive Summary", range: "A1:N34", scale: 1.4, format: "png" });
await fs.writeFile(`${base}/docs/images/excel_executive_summary.png`, new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`Saved ${outputPath}`);
