#!/usr/bin/env python3
"""
make_free_edition.py -- build the FREE edition of the Chicago Open Building Violations list.

Input : the FULL CSV written by fetch_chicago_violations.py
        (17 columns, one row per property, violation_status = OPEN, repair-type items only)
Output: the data/ folder of this repository

  chicago_open_violations_FREE_<pull-date>.csv    15 columns, UTF-8 with BOM (Excel-safe)
  chicago_open_violations_FREE_<pull-date>.xlsx   sheets: Properties / README / Column_Dictionary / Stats
  SAMPLE_25_rows.md                                markdown table for a forum / Reddit post body
  CHANGELOG.md                                     prepends one entry per pull
  stats.json                                       machine-readable summary (all counts measured from the FULL CSV)
  QA_REPORT_<window-start>.txt                     copied from the fetch run      (--qa)
  extras/cook_county_estate_of_SAMPLE_20_rows.csv  copied as-is                   (--estate-sample)
  extras/cook_county_estate_of_SAMPLE_20_rows.md   markdown table of that sample  (--estate-sample)
  ../docs/column_dictionary.md                     same dictionary as the XLSX sheet (--docs)

Dependencies: Python 3.8+ standard library + openpyxl.

Example (run from the repo root):
  python tools/make_free_edition.py \
      --full  ../delivery-engine/jobs/chicago-building-violations/out/2026-10-13/Chicago_Open_Building_Violations_2026-07-13_FULL.csv \
      --qa    ../delivery-engine/jobs/chicago-building-violations/out/2026-10-13/QA_REPORT_2026-07-13.txt \
      --estate-sample ../delivery-engine/jobs/cook-county-estate-of/out/2026-10-13/Cook_County_Estate_Of_SAMPLE_20_rows.csv \
      --estate-full   ../delivery-engine/jobs/cook-county-estate-of/out/2026-10-13/Cook_County_Estate_Of_2026_FULL.csv \
      --pull-date 2026-10-13 --docs
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import shutil
import sys
from collections import Counter, OrderedDict

try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
except ImportError:  # pragma: no cover
    sys.exit("openpyxl is required:  pip install openpyxl")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))

DATASET = "22u3-xenr"
DATASET_URL = "https://data.cityofchicago.org/d/22u3-xenr"
DROP = ("violation_codes", "property_group")
INT_COLS = ("open_work_violation_count", "structural", "envelope", "mechanical")
FLOAT_COLS = ("latitude", "longitude")
DATE_COLS = ("earliest_open_date", "latest_open_date")

AI_DISCLOSURE = (
    "Built with an AI coding agent (Claude Code); data pulled from the City of Chicago / "
    "Cook County open-data APIs; every row links to the original public record; "
    "no phone numbers, no emails, no skip tracing."
)

# One sentence per column + the type.  Examples are filled from the first data row at run time.
DICTIONARY = OrderedDict([
    ("property_key", ("text",
        "Upper-cased canonical address used to group violations into one row per property; "
        "in practice identical to the city's `address` field.")),
    ("address", ("text",
        "Street address exactly as it appears in the City of Chicago Building Violations dataset.")),
    ("city", ("text", "Always 'Chicago'.")),
    ("state", ("text", "Always 'IL'.")),
    ("open_work_violation_count", ("integer",
        "Number of OPEN violations at this address, dated inside the pull window, that require physical "
        "repair work (structural + envelope). Paperwork-only items are excluded.")),
    ("primary_category", ("text",
        "Worst category present at the address: STRUCTURAL if at least one structural item is open, "
        "otherwise ENVELOPE.")),
    ("structural", ("integer",
        "Count of OPEN structural items (porch, roof, masonry, foundation, stairs, parapet, chimney, "
        "garage, lintel, joist, fire escape ...).")),
    ("envelope", ("integer",
        "Count of OPEN exterior-envelope / finish items (windows, exterior doors, siding, gutters, "
        "downspouts, fences, plaster, ceilings, tuckpointing ...).")),
    ("mechanical", ("integer",
        "Count of OPEN mechanical items (boiler, elevator, plumbing, wiring). Always 0 in this edition "
        "because mechanical items are not kept.")),
    ("violation_types", ("text",
        "Distinct violation descriptions at the address, most frequent first, separated by ';'. "
        "Truncated at 600 characters.")),
    ("earliest_open_date", ("date",
        "Earliest violation_date among the kept OPEN items at this address (YYYY-MM-DD).")),
    ("latest_open_date", ("date",
        "Latest violation_date among the kept OPEN items at this address (YYYY-MM-DD).")),
    ("latitude", ("decimal",
        "Latitude as published by the city; blank for a few addresses the city has not geocoded.")),
    ("longitude", ("decimal",
        "Longitude as published by the city; blank for a few addresses the city has not geocoded.")),
    ("source_url", ("url",
        "Live SODA API query that returns every OPEN violation the city currently lists at this exact "
        "address. Open it in a browser to verify the row against the original public record.")),
])

XLSX_WIDTHS = {
    "property_key": 30, "address": 30, "city": 9, "state": 6,
    "open_work_violation_count": 12, "primary_category": 16, "structural": 11, "envelope": 10,
    "mechanical": 11, "violation_types": 80, "earliest_open_date": 14, "latest_open_date": 14,
    "latitude": 13, "longitude": 13, "source_url": 13,
}

# Cook County Assessor major class -> plain-English group (used for the extras sample)
CLASS_GROUPS = (
    ("1", "Vacant land"),
    ("2", "Residential (6 units or less)"),
    ("3", "Multi-family 7+"),
    ("5", "Commercial/Industrial"),
    ("E", "Exempt"),
)


# ----------------------------------------------------------------------------- helpers
def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        rows = list(rd)
    return rd.fieldnames, rows


def write_csv_bom(path, fields, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def md_cell(s):
    return (s or "").replace("|", "\\|").replace("\n", " ").strip()


def fmt_int(n):
    return "{:,}".format(n)


def next_friday(d):
    days = (4 - d.weekday()) % 7
    return d + dt.timedelta(days=days or 7)


def parse_qa(path):
    """Pull the two headline counts out of QA_REPORT_<cutoff>.txt (optional)."""
    out = {}
    if not path or not os.path.exists(path):
        return out
    txt = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r"Raw violation rows scanned\s*:\s*([\d,]+)", txt)
    if m:
        out["raw_rows_scanned"] = int(m.group(1).replace(",", ""))
    m = re.search(r"Construction-relevant rows\s*:\s*([\d,]+)", txt)
    if m:
        out["repair_type_rows_kept"] = int(m.group(1).replace(",", ""))
    return out


def class_group(code):
    c = (code or "").strip().upper()
    for prefix, label in CLASS_GROUPS:
        if c.startswith(prefix):
            return label
    return ("Other (class %s)" % c) if c else ""


# ----------------------------------------------------------------------------- stats
def compute_stats(rows, fields, pull_date, window_start, qa_counts):
    n = len(rows)
    counts = [int(r["open_work_violation_count"] or 0) for r in rows]
    structural_rows = sum(int(r["structural"] or 0) for r in rows)
    envelope_rows = sum(int(r["envelope"] or 0) for r in rows)
    mechanical_rows = sum(int(r["mechanical"] or 0) for r in rows)
    by_cat = Counter((r["primary_category"] or "").strip() for r in rows)
    earliest = min(r["earliest_open_date"] for r in rows if r["earliest_open_date"])
    latest = max(r["latest_open_date"] for r in rows if r["latest_open_date"])
    types = Counter()
    for r in rows:
        for t in (r["violation_types"] or "").split(";"):
            t = t.strip()
            if t:
                types[t] += 1
    blanks = OrderedDict((c, sum(1 for r in rows if (r.get(c) or "").strip() == "")) for c in fields)
    dup_addresses = sum(1 for _, k in Counter(r["address"].strip().upper() for r in rows).items() if k > 1)

    stats = OrderedDict()
    stats["edition"] = "FREE"
    stats["pull_date"] = pull_date
    stats["dataset"] = "%s Building Violations (data.cityofchicago.org)" % DATASET
    stats["filter"] = "violation_status = OPEN AND violation_date > %s" % window_start
    stats["window_start"] = window_start
    stats["window_end"] = pull_date
    stats["kept_categories"] = ["STRUCTURAL", "ENVELOPE"]
    stats["properties"] = n
    stats["columns"] = len(fields)
    stats["kept_violation_rows_total"] = structural_rows + envelope_rows + mechanical_rows
    stats["kept_violation_rows_structural"] = structural_rows
    stats["kept_violation_rows_envelope"] = envelope_rows
    stats["kept_violation_rows_mechanical"] = mechanical_rows
    stats["properties_by_primary_category"] = OrderedDict(sorted(by_cat.items(), key=lambda kv: -kv[1]))
    stats["properties_with_3plus_open_work_violations"] = sum(1 for c in counts if c >= 3)
    stats["max_open_work_violations_on_one_property"] = max(counts) if counts else 0
    stats["earliest_violation_date"] = earliest
    stats["latest_violation_date"] = latest
    stats["top_10_violation_types"] = [OrderedDict([("violation_type", t), ("properties", c)])
                                       for t, c in types.most_common(10)]
    stats["distinct_violation_types"] = len(types)
    stats["duplicate_addresses"] = dup_addresses
    stats["blank_cells_per_column"] = blanks
    for k, v in qa_counts.items():
        stats[k] = v
    stats["generated_at"] = dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    stats["generator"] = "tools/make_free_edition.py"
    return stats


# ----------------------------------------------------------------------------- README text (shared by xlsx + md)
def readme_lines(stats):
    s = stats
    return [
        "Chicago Open Building Violations -- Repair-Needed Properties (FREE edition)",
        "",
        "Chicago properties with OPEN structural / exterior building violations. One row per address, "
        "every row links back to the city record.",
        "",
        "Release: %s   Properties: %s   Window: violations dated after %s (pulled %s)   Columns: %d"
        % (s["pull_date"], fmt_int(s["properties"]), s["window_start"], s["pull_date"], s["columns"]),
        "",
        "WHO IT IS FOR",
        "Wholesalers, flippers and contractors building mailers, driving-for-dollars routes or bid lists "
        "for properties that need physical repair work.",
        "",
        "WHAT IS IN IT",
        "- Source: City of Chicago Data Portal, dataset %s (Building Violations), via the public SODA API. "
        "No scraping, no login, no API key." % DATASET,
        "- Filter: violation_status = OPEN and violation_date after %s." % s["window_start"],
        "- Kept only violations that mean physical repair work (porch, roof, masonry, windows, doors, "
        "fences ...); dropped paperwork items (register, arrange inspection, smoke detectors, weeds, "
        "permits, rodents).",
        "- Aggregated to one row per address. Ranked: most structural + envelope work first, then by "
        "total open items, then most recent.",
        "- %s properties; %s kept violation rows (%s STRUCTURAL, %s ENVELOPE)."
        % (fmt_int(s["properties"]), fmt_int(s["kept_violation_rows_total"]),
           fmt_int(s["kept_violation_rows_structural"]), fmt_int(s["kept_violation_rows_envelope"])),
        "",
        "HOW IT WAS BUILT",
        AI_DISCLOSURE,
        "Method, classification rules and query URLs: docs/method.md in the GitHub repository.",
        "",
        "LIMITATIONS (please read)",
        "- OPEN status lags compliance: the city closes a violation only after a re-inspection, so some "
        "listed items are already fixed. Click source_url to see the live status before acting.",
        "- Address-level, not parcel (PIN) level: a multi-unit building is one row; no owner data.",
        "- 3-month window only; violations opened before %s are not included even if still OPEN."
        % s["window_start"],
        "- Classification is keyword based (regular expressions on violation_description). Edge cases "
        "exist; the dropped-item list is in the QA report.",
        "- Counts measure how many open items the inspector wrote up, not dollar severity.",
        "- The city updates the dataset daily; this file is refreshed on Fridays.",
        "",
        "WHAT THIS IS NOT",
        "No owner names, no phone numbers, no emails, no skip tracing. Public records only.",
        "",
        "LICENSE",
        "Creative Commons Attribution 4.0 (CC BY 4.0). Attribution: 'Chicago Open Building Violations "
        "free edition (GitHub repository chicago-open-violations-leads); data from the City of Chicago "
        "Data Portal dataset %s'. No warranty." % DATASET,
        "",
        "Paid editions (owner of record, Cook County Estate-of parcels, DIY Socrata kit) and a tip jar "
        "are linked at the bottom of the repository README.",
    ]


# ----------------------------------------------------------------------------- XLSX
def write_xlsx(path, fields, rows, stats):
    wb = Workbook()
    hdr_font = Font(bold=True)
    hdr_fill = PatternFill("solid", fgColor="DDEBF7")

    # --- Properties
    ws = wb.active
    ws.title = "Properties"
    ws.append(fields)
    for c in ws[1]:
        c.font = hdr_font
        c.fill = hdr_fill
    url_idx = fields.index("source_url") + 1
    date_idx = [fields.index(c) + 1 for c in DATE_COLS if c in fields]
    for r in rows:
        out = []
        for c in fields:
            v = r.get(c, "")
            if c in INT_COLS:
                v = int(v) if v not in ("", None) else None
            elif c in FLOAT_COLS:
                v = float(v) if v not in ("", None) else None
            elif c in DATE_COLS:
                v = dt.date.fromisoformat(v[:10]) if v else None
            elif c == "source_url":
                v = "city record"
            out.append(v)
        ws.append(out)
    for i, r in enumerate(rows, start=2):
        cell = ws.cell(row=i, column=url_idx)
        cell.hyperlink = r["source_url"]
        cell.style = "Hyperlink"
        for di in date_idx:
            ws.cell(row=i, column=di).number_format = "yyyy-mm-dd"
    for i, c in enumerate(fields, start=1):
        ws.column_dimensions[get_column_letter(i)].width = XLSX_WIDTHS.get(c, 14)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    # --- README
    ws2 = wb.create_sheet("README")
    ws2.column_dimensions["A"].width = 120
    for line in readme_lines(stats):
        ws2.append([line])
    for row in ws2.iter_rows():
        row[0].alignment = Alignment(wrap_text=True, vertical="top")
    ws2["A1"].font = Font(bold=True, size=13)

    # --- Column_Dictionary
    ws3 = wb.create_sheet("Column_Dictionary")
    ws3.append(["column", "type", "description", "example"])
    for c in ws3[1]:
        c.font = hdr_font
        c.fill = hdr_fill
    example = rows[0] if rows else {}
    for col in fields:
        typ, desc = DICTIONARY.get(col, ("text", ""))
        ex = example.get(col, "")
        if col == "violation_types" and len(ex) > 120:
            ex = ex[:117] + "..."
        ws3.append([col, typ, desc, ex])
    for col_letter, w in (("A", 28), ("B", 10), ("C", 95), ("D", 60)):
        ws3.column_dimensions[col_letter].width = w
    for row in ws3.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws3.freeze_panes = "A2"

    # --- Stats
    ws4 = wb.create_sheet("Stats")
    ws4.column_dimensions["A"].width = 46
    ws4.column_dimensions["B"].width = 60
    ws4.append(["metric", "value"])
    for c in ws4[1]:
        c.font = hdr_font
        c.fill = hdr_fill
    scalar_keys = ["edition", "pull_date", "dataset", "filter", "window_start", "window_end",
                   "properties", "columns", "kept_violation_rows_total",
                   "kept_violation_rows_structural", "kept_violation_rows_envelope",
                   "kept_violation_rows_mechanical", "properties_with_3plus_open_work_violations",
                   "max_open_work_violations_on_one_property", "earliest_violation_date",
                   "latest_violation_date", "distinct_violation_types", "duplicate_addresses",
                   "raw_rows_scanned", "repair_type_rows_kept", "generated_at"]
    for k in scalar_keys:
        if k in stats:
            v = stats[k]
            ws4.append([k, ", ".join(v) if isinstance(v, list) else v])
    ws4.append([])
    ws4.append(["properties_by_primary_category", "properties"])
    ws4.cell(row=ws4.max_row, column=1).font = hdr_font
    for k, v in stats["properties_by_primary_category"].items():
        ws4.append([k, v])
    ws4.append([])
    ws4.append(["top_10_violation_types", "properties"])
    ws4.cell(row=ws4.max_row, column=1).font = hdr_font
    for item in stats["top_10_violation_types"]:
        ws4.append([item["violation_type"], item["properties"]])
    ws4.append([])
    ws4.append(["blank_cells_per_column", "blank cells"])
    ws4.cell(row=ws4.max_row, column=1).font = hdr_font
    for k, v in stats["blank_cells_per_column"].items():
        ws4.append([k, v])

    wb.save(path)


# ----------------------------------------------------------------------------- markdown sample
def pick_top(rows, n):
    # Same ranking as the released CSV (and the fetch script that writes the FULL file):
    # structural + envelope desc, total open items desc, latest violation date desc, structural desc.
    # The sort is stable, so complete ties keep the file order -- the sample is exactly the top of the CSV.
    ranked = sorted(rows, key=lambda r: (int(r["structural"] or 0) + int(r["envelope"] or 0),
                                         int(r["open_work_violation_count"] or 0),
                                         r["latest_open_date"] or "",
                                         int(r["structural"] or 0)), reverse=True)
    seen, pick = set(), []
    for r in ranked:
        key = r["address"].strip().upper()
        if key in seen:
            continue
        seen.add(key)
        pick.append(r)
        if len(pick) == n:
            break
    return pick


def write_sample_md(path, rows, n, stats):
    pick = pick_top(rows, n)
    lines = [
        "**Top %d of %s Chicago properties with OPEN repair-type building violations** "
        "(city data pulled %s; violations dated after %s; one row per address; the first %d rows of the "
        "full file -- ranked by number of open repair items, most recent violation first on ties)"
        % (len(pick), fmt_int(stats["properties"]), stats["pull_date"], stats["window_start"], len(pick)),
        "",
        "| Address | Open work violations | Main category | Top violation types (first 3) | Latest violation date |",
        "|---|---:|---|---|---|",
    ]
    for r in pick:
        types = [t.strip() for t in (r["violation_types"] or "").split(";") if t.strip()][:3]
        lines.append("| %s | %s | %s | %s | %s |" % (
            md_cell(r["address"]), r["open_work_violation_count"], md_cell(r["primary_category"]),
            md_cell("; ".join(types)), r["latest_open_date"]))
    lines += [
        "",
        "Data source: City of Chicago Data Portal, dataset %s (Building Violations), filter "
        "violation_status = OPEN. Kept only violations that require physical repair work; dropped "
        "paperwork items. Public records only -- no owner names, phone numbers or emails. Built with an "
        "AI coding agent (Claude Code); every row in the full file links back to the city record."
        % DATASET,
        "",
    ]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    return len(pick)


# ----------------------------------------------------------------------------- changelog
def update_changelog(path, stats, csv_name, xlsx_name, qa_name, next_refresh):
    entry = [
        "## %s -- initial pull: %s properties (window %s -> %s)"
        % (stats["pull_date"], fmt_int(stats["properties"]), stats["window_start"], stats["window_end"]),
        "",
        "- Source: City of Chicago dataset %s, violation_status = OPEN, violation_date > %s"
        % (DATASET, stats["window_start"]),
    ]
    if "raw_rows_scanned" in stats and "repair_type_rows_kept" in stats:
        entry.append("- Raw OPEN violation rows scanned: %s; repair-type rows kept: %s; unique properties: %s"
                     % (fmt_int(stats["raw_rows_scanned"]), fmt_int(stats["repair_type_rows_kept"]),
                        fmt_int(stats["properties"])))
    else:
        entry.append("- Kept violation rows: %s; unique properties: %s"
                     % (fmt_int(stats["kept_violation_rows_total"]), fmt_int(stats["properties"])))
    entry += [
        "- Primary category: " + ", ".join("%s %s" % (k, fmt_int(v))
                                           for k, v in stats["properties_by_primary_category"].items()),
        "- Files: %s, %s, SAMPLE_25_rows.md, %s, stats.json" % (csv_name, xlsx_name, qa_name or "QA report"),
        "- Next scheduled refresh: Friday %s" % next_refresh,
        "",
    ]
    header = ["# Changelog", "",
              "One entry per data pull. Dates are the day the city data was pulled. Counts are measured "
              "from the released file, not estimated.", ""]
    existing = ""
    if os.path.exists(path):
        existing = open(path, encoding="utf-8").read()
        # drop the header block so it is written once
        existing = re.sub(r"^# Changelog\n\n.*?\n\n", "", existing, count=1, flags=re.S)
        # if this pull date already has an entry, replace it instead of duplicating
        existing = re.sub(r"## %s --.*?(?=\n## |\Z)" % re.escape(stats["pull_date"]), "", existing,
                          flags=re.S).lstrip("\n")
        if existing:
            entry[0] = entry[0].replace("initial pull", "refresh")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(header + entry) + ("\n" + existing if existing else ""))


# ----------------------------------------------------------------------------- docs/column_dictionary.md
def write_column_dictionary_md(path, fields, rows, stats):
    example = rows[0] if rows else {}
    lines = [
        "# Column dictionary -- FREE edition (%d columns)" % len(fields),
        "",
        "One row per property (address). Release %s, %s rows. Examples come from the first row of the file."
        % (stats["pull_date"], fmt_int(stats["properties"])),
        "",
        "| # | Column | Type | Description | Example |",
        "|---:|---|---|---|---|",
    ]
    for i, col in enumerate(fields, start=1):
        typ, desc = DICTIONARY.get(col, ("text", ""))
        ex = example.get(col, "")
        if col == "violation_types" and len(ex) > 90:
            ex = ex[:87] + "..."
        if col == "source_url":
            ex = "`" + ex[:60] + "...`"
        else:
            ex = md_cell(ex)
        lines.append("| %d | `%s` | %s | %s | %s |" % (i, col, typ, md_cell(desc), ex))
    lines += [
        "",
        "## Columns removed from the FULL build",
        "",
        "| Column | Why it is not in the free edition |",
        "|---|---|",
        "| `violation_codes` | City violation code list (e.g. `CN061014;CN065034`). Redundant with `violation_types` for outreach use. |",
        "| `property_group` | City's internal building-group id. Not useful without the city's own join tables. |",
        "",
        "## Notes",
        "",
        "- Blank cells in this release: " + ", ".join("`%s` %d" % (k, v) for k, v in
                                                     stats["blank_cells_per_column"].items() if v) +
        (" (all other columns 0)." if any(stats["blank_cells_per_column"].values()) else "none."),
        "- `mechanical` is always 0 in the free edition; the column is kept so the layout matches the paid editions.",
        "- Dates are ISO `YYYY-MM-DD` text in the CSV and real date cells in the XLSX.",
        "- `source_url` in the XLSX shows the text *city record* and carries the URL as a hyperlink; the CSV has the raw URL.",
        "",
    ]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


# ----------------------------------------------------------------------------- Cook County extras sample
def write_estate_sample(sample_csv, full_csv, extras_dir):
    os.makedirs(extras_dir, exist_ok=True)
    dst_csv = os.path.join(extras_dir, "cook_county_estate_of_SAMPLE_20_rows.csv")
    shutil.copyfile(sample_csv, dst_csv)
    fields, rows = read_csv(sample_csv)

    total = high = medium = None
    if full_csv and os.path.exists(full_csv):
        _, full_rows = read_csv(full_csv)
        total = len(full_rows)
        high = sum(1 for r in full_rows if (r.get("confidence") or "").upper() == "HIGH")
        medium = sum(1 for r in full_rows if (r.get("confidence") or "").upper() == "MEDIUM")

    head = ("**Sample: %d Cook County parcels where the 2026 tax roll lists the taxpayer or owner as "
            "'Estate of ...'**" % len(rows))
    if total is not None:
        head += (" -- full list %s parcels (%s HIGH / %s MEDIUM confidence). Sample = residential, not sold "
                 "since 2025-01-01, HIGH first, one per surname, max two per municipality."
                 % (fmt_int(total), fmt_int(high), fmt_int(medium)))
    lines = [
        head,
        "",
        "| PIN | Property address | Municipality | Class group | Confidence | Mailing city/state |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        mail = ", ".join(x for x in ((r.get("mailing_city") or "").strip(),
                                     (r.get("mailing_state") or "").strip()) if x)
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            md_cell(r.get("pin")), md_cell(r.get("property_address")), md_cell(r.get("municipality")),
            class_group(r.get("class")), md_cell(r.get("confidence")), md_cell(mail)))
    lines += [
        "",
        "Class group = Cook County Assessor major class: 1xx Vacant land; 2xx Residential (6 units or less); "
        "3xx Multi-family 7+; 5xx Commercial/Industrial; Exx Exempt.",
        "",
        "Sources: Cook County Assessor open data -- 3723-97qp (Parcel Addresses: taxpayer + owner names), "
        "pabr-t5kh (Parcel Universe: class, township, municipality), wvhk-k5uv (Parcel Sales since "
        "2025-01-01). Confidence HIGH = both taxpayer and owner name read 'Estate of'; MEDIUM = one of them, "
        "or an executor / administrator name. This is a floor, not a census: the county changes a taxpayer "
        "name to 'Estate of' only when it is notified. PINs are 14-digit strings -- open the CSV with the "
        "PIN column as text or the leading zero is lost. " + AI_DISCLOSURE,
        "",
    ]
    dst_md = os.path.join(extras_dir, "cook_county_estate_of_SAMPLE_20_rows.md")
    with open(dst_md, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    return dst_csv, dst_md, len(rows)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--full", required=True, help="Chicago_Open_Building_Violations_<cutoff>_FULL.csv")
    ap.add_argument("--out", default=os.path.join(REPO, "data"), help="output folder (default: <repo>/data)")
    ap.add_argument("--pull-date", default=dt.date.today().isoformat(), help="YYYY-MM-DD the data was pulled")
    ap.add_argument("--window-start", help="YYYY-MM-DD cutoff used in the pull (default: parsed from --full name)")
    ap.add_argument("--qa", help="QA_REPORT_<cutoff>.txt from the fetch run; copied into data/ and parsed for counts")
    ap.add_argument("--sample-rows", type=int, default=25)
    ap.add_argument("--estate-sample", help="Cook_County_Estate_Of_SAMPLE_20_rows.csv -> data/extras/")
    ap.add_argument("--estate-full", help="Cook_County_Estate_Of_<year>_FULL.csv (only counted, never copied)")
    ap.add_argument("--docs", action="store_true", help="also write <repo>/docs/column_dictionary.md")
    ap.add_argument("--next-refresh",
                    help="YYYY-MM-DD (a Friday) written to CHANGELOG.md as the next scheduled refresh "
                         "(default: the first Friday after the later of --pull-date and today)")
    a = ap.parse_args()

    window_start = a.window_start
    if not window_start:
        m = re.search(r"_(\d{4}-\d{2}-\d{2})_FULL", os.path.basename(a.full))
        if not m:
            sys.exit("cannot infer --window-start from file name; pass it explicitly")
        window_start = m.group(1)
    pull_day = dt.date.fromisoformat(a.pull_date)
    dt.date.fromisoformat(window_start)
    next_refresh = a.next_refresh or next_friday(max(pull_day, dt.date.today())).isoformat()
    if dt.date.fromisoformat(next_refresh).weekday() != 4:
        sys.exit("--next-refresh must be a Friday, got %s" % next_refresh)

    os.makedirs(a.out, exist_ok=True)
    fields_in, rows = read_csv(a.full)
    missing = [c for c in DICTIONARY if c not in fields_in]
    if missing:
        sys.exit("FULL file is missing expected columns: %s" % missing)
    fields = [c for c in fields_in if c not in DROP]
    if len(fields) != 15:
        sys.exit("expected 15 columns after dropping %s, got %d: %s" % (DROP, len(fields), fields))

    qa_counts = parse_qa(a.qa)
    stats = compute_stats(rows, fields, a.pull_date, window_start, qa_counts)

    csv_name = "chicago_open_violations_FREE_%s.csv" % a.pull_date
    xlsx_name = "chicago_open_violations_FREE_%s.xlsx" % a.pull_date
    write_csv_bom(os.path.join(a.out, csv_name), fields, rows)
    write_xlsx(os.path.join(a.out, xlsx_name), fields, rows, stats)
    n_sample = write_sample_md(os.path.join(a.out, "SAMPLE_%d_rows.md" % a.sample_rows), rows, a.sample_rows, stats)

    qa_name = None
    if a.qa and os.path.exists(a.qa):
        qa_name = os.path.basename(a.qa)
        shutil.copyfile(a.qa, os.path.join(a.out, qa_name))
    update_changelog(os.path.join(a.out, "CHANGELOG.md"), stats, csv_name, xlsx_name, qa_name, next_refresh)
    with open(os.path.join(a.out, "stats.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
        f.write("\n")

    if a.docs:
        docs_dir = os.path.join(REPO, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        write_column_dictionary_md(os.path.join(docs_dir, "column_dictionary.md"), fields, rows, stats)

    if a.estate_sample:
        dst_csv, dst_md, n_est = write_estate_sample(a.estate_sample, a.estate_full, os.path.join(a.out, "extras"))
        print("extras : %s (%d rows), %s" % (dst_csv, n_est, dst_md))

    print("FREE edition written to %s" % a.out)
    print("  properties=%d columns=%d sample_rows=%d" % (len(rows), len(fields), n_sample))
    print("  kept rows: structural=%d envelope=%d mechanical=%d" % (
        stats["kept_violation_rows_structural"], stats["kept_violation_rows_envelope"],
        stats["kept_violation_rows_mechanical"]))
    print("  by primary_category: %s" % dict(stats["properties_by_primary_category"]))
    print("  dates: %s .. %s" % (stats["earliest_violation_date"], stats["latest_violation_date"]))
    print("  blanks: %s" % {k: v for k, v in stats["blank_cells_per_column"].items() if v})
    print("  next scheduled refresh: Friday %s" % next_refresh)


if __name__ == "__main__":
    main()
