#!/usr/bin/env python3
"""Rewrite the data-dependent parts of README.md from data/stats.json and the QA report.

Run after tools/make_free_edition.py:
    python tools/update_readme.py --next-refresh 2026-10-30

Everything else in README.md is left untouched. The blocks are delimited by HTML comment markers
(inserted on first run) so later refreshes are deterministic.
"""
import argparse, datetime as dt, glob, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(REPO, "README.md")
STATS = os.path.join(REPO, "data", "stats.json")

def fmt(n): return f"{n:,}"

def admin_itemised_rows(qa_path):
    """Sum of the explicitly dropped (ADMIN) descriptions listed in the QA report."""
    txt = open(qa_path, encoding="utf-8").read()
    if "Top dropped administrative" not in txt: return None, 0
    sec = txt.split("Top dropped administrative / non-construction descriptions:")[1]
    counts = [int(m.group(1)) for m in re.finditer(r"^\s+(\d+)\s+\S", sec, re.M)]
    return sum(counts), len(counts)

def weekday(d): return dt.date.fromisoformat(d).strftime("%A")

def block(name, body):
    return f"<!-- {name}:start -->\n{body}\n<!-- {name}:end -->"

def replace_block(text, name, body, first_run_pattern):
    marked = re.compile(rf"<!-- {name}:start -->.*?<!-- {name}:end -->", re.S)
    if marked.search(text):
        return marked.sub(lambda _: block(name, body), text)
    m = first_run_pattern.search(text)
    if not m:
        sys.exit(f"README: could not locate the '{name}' section for the first run")
    return text[:m.start()] + block(name, body) + text[m.end():]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--next-refresh", required=True, help="YYYY-MM-DD (a Friday)")
    a = ap.parse_args()
    if dt.date.fromisoformat(a.next_refresh).weekday() != 4:
        sys.exit("--next-refresh must be a Friday")

    s = json.load(open(STATS, encoding="utf-8"))
    pull, ws = s["pull_date"], s["window_start"]
    csv_name = f"chicago_open_violations_FREE_{pull}.csv"
    xlsx_name = f"chicago_open_violations_FREE_{pull}.xlsx"
    qa_candidates = sorted(glob.glob(os.path.join(REPO, "data", "QA_REPORT_*.txt")))
    if not qa_candidates: sys.exit("no QA report in data/")
    qa_path = qa_candidates[-1]; qa_name = os.path.basename(qa_path)
    admin_sum, admin_n = admin_itemised_rows(qa_path)
    raw, kept = s["raw_rows_scanned"], s["kept_violation_rows_total"]
    dropped = raw - kept
    cats = s["properties_by_primary_category"]
    blanks = {k: v for k, v in s["blank_cells_per_column"].items() if v}
    top = ", ".join(f"{t['violation_type']} ({fmt(t['properties'])}{' properties' if i == 0 else ''})" for i, t in enumerate(s["top_10_violation_types"]))
    if blanks:
        blank_txt = "no blanks except " + ", ".join(f"`{k}` ({v})" for k, v in blanks.items()) + " where the city has not geocoded the address"
    else:
        blank_txt = "no blank cells"

    text = open(README, encoding="utf-8").read()

    release = (f"**Current release: {pull} — {fmt(s['properties'])} properties · violations dated after {ws} · "
               f"{s['columns']} columns · one row per address.** History: [data/CHANGELOG.md](data/CHANGELOG.md).")
    text = replace_block(text, "release", release, re.compile(r"\*\*Current release: .*?\*\* History: \[data/CHANGELOG\.md\]\(data/CHANGELOG\.md\)\."))

    files = (f"| [{csv_name}](data/{csv_name}) | {fmt(s['properties'])} rows × {s['columns']} columns, UTF-8 with BOM (opens cleanly in Excel, Google Sheets, Numbers) |\n"
             f"| [{xlsx_name}](data/{xlsx_name}) | Same data with filters and frozen header, plus README / Column_Dictionary / Stats sheets; `source_url` is a clickable **city record** link |\n"
             f"| [SAMPLE_25_rows.md](data/SAMPLE_25_rows.md) | The first 25 rows of the CSV — the properties with the most open repair items (ties broken by the most recent violation) — as a markdown table |\n"
             f"| [{qa_name}](data/{qa_name}) | Row counts, blank-cell audit and the list of dropped paperwork items from the pull |")
    text = replace_block(text, "files", files, re.compile(r"\| \[chicago_open_violations_FREE_[^\n]*\n\| \[chicago_open_violations_FREE_[^\n]*\n\| \[SAMPLE_25_rows\.md\][^\n]*\n\| \[QA_REPORT_[^\n]*"))

    whats = (f"- **{fmt(s['properties'])} properties** with at least one OPEN repair-type violation dated after {ws} (pulled {pull}; actual violation dates run {s['earliest_violation_date']} → {s['latest_violation_date']}).\n"
             f"- **{fmt(kept)} kept violation rows** — {fmt(s['kept_violation_rows_structural'])} STRUCTURAL, {fmt(s['kept_violation_rows_envelope'])} ENVELOPE — out of {fmt(raw)} OPEN rows the city listed for the window. The other {fmt(dropped)} rows were not kept, for three different reasons: explicit paperwork and housekeeping items (arrange inspection, register vacant building, smoke detectors, weeds, rodents, permits — the {admin_n} most frequent are itemised in the QA report and add up to {fmt(admin_sum)} rows); mechanical items (elevators, boilers, wiring — excluded by design); and descriptions the keyword rules do not classify, which include some generic repair wording (REPAIR OR REPLACE, REPAIR FLOOR, REPAIR SCREENS, REPAIR LINTELS). A property whose only open items fall in those groups is not in this list — see [docs/method.md](docs/method.md).\n"
             f"- **Primary category:** {fmt(cats.get('STRUCTURAL', 0))} properties STRUCTURAL, {fmt(cats.get('ENVELOPE', 0))} ENVELOPE. {fmt(s['properties_with_3plus_open_work_violations'])} properties have 3 or more open repair items; the maximum on one address is {s['max_open_work_violations_on_one_property']}.\n"
             f"- **Ranking:** most structural + envelope work first, then total open items, then most recent — the top of the file is the heaviest work.\n"
             f"- **{s['columns']} columns**, {blank_txt}.\n"
             f"- **Most common open items:** {top}.")
    text = replace_block(text, "whats", whats, re.compile(r"- \*\*[\d,]+ properties\*\* with at least one OPEN repair-type violation.*?- \*\*Most common open items:\*\*[^\n]*", re.S))

    refresh = (f"Every **Friday**. Each refresh replaces the dated CSV/XLSX in `data/`, updates `stats.json` and the QA report, and adds a CHANGELOG entry with the new counts (older files stay in git history). "
               f"Current data: the pull of {weekday(pull)} {pull}. **Next refresh: Friday {a.next_refresh}.**")
    text = replace_block(text, "refresh", refresh, re.compile(r"Every \*\*Friday\*\*\. Each refresh replaces .*?\*\*Next refresh: Friday \d{4}-\d{2}-\d{2}\.\*\*", re.S))

    open(README, "w", encoding="utf-8", newline="\n").write(text)
    print(f"README updated: {s['properties']} properties, pull {pull}, next refresh {a.next_refresh}")

if __name__ == "__main__":
    main()
