# Chicago Open Building Violations — Repair-Needed Properties (free edition)

Chicago properties with OPEN structural / exterior building violations — refreshed on Fridays, free, every row links to the city record.

<!-- release:start -->
**Current release: 2026-10-22 — 1,224 properties · violations dated after 2026-07-22 · 15 columns · one row per address.** History: [data/CHANGELOG.md](data/CHANGELOG.md).
<!-- release:end -->

## What this is

The City of Chicago publishes every building-code violation its inspectors write up. This repository filters that feed down to the part a rehabber or wholesaler cares about — violations that are still **OPEN** and that mean **physical repair work** (porch, roof, masonry, foundation, stairs, windows, doors, siding, fences, plaster) — and rolls it up to one row per address with counts, the violation descriptions in plain text, first/last violation date, coordinates, and a `source_url` that re-runs the city query for that exact address so you can check the live record before you act.

The Chicago violation files are a list of **properties**, not people: no owner names, phone numbers or emails. The one exception in this repository is the 20-row Cook County *Estate-of* sample in [data/extras/](data/extras/), which carries public tax-roll taxpayer names and mailing addresses exactly as the Cook County Assessor publishes them (still no phone numbers, emails or skip tracing) — see [Requests](#requests).

## Who it's for

- Wholesalers and flippers building a mailer or a driving-for-dollars route of properties that visibly need work.
- Contractors and remodelers who want a bid list of buildings with open repair orders.
- Anyone who wants the city's own data without paying a list vendor for it.

## Download

| File | What it is |
|---|---|
<!-- files:start -->
| [chicago_open_violations_FREE_2026-10-22.csv](data/chicago_open_violations_FREE_2026-10-22.csv) | 1,224 rows × 15 columns, UTF-8 with BOM (opens cleanly in Excel, Google Sheets, Numbers) |
| [chicago_open_violations_FREE_2026-10-22.xlsx](data/chicago_open_violations_FREE_2026-10-22.xlsx) | Same data with filters and frozen header, plus README / Column_Dictionary / Stats sheets; `source_url` is a clickable **city record** link |
| [SAMPLE_25_rows.md](data/SAMPLE_25_rows.md) | The first 25 rows of the CSV — the properties with the most open repair items (ties broken by the most recent violation) — as a markdown table |
| [QA_REPORT_2026-07-22.txt](data/QA_REPORT_2026-07-22.txt) | Row counts, blank-cell audit and the list of dropped paperwork items from the pull |
<!-- files:end -->
| [stats.json](data/stats.json) | Machine-readable summary (all counts measured from the released file) |
| [CHANGELOG.md](data/CHANGELOG.md) | One entry per pull |

On GitHub, open a file and use **Download raw file** (the icon next to *Raw*).

## What's in it

<!-- whats:start -->
- **1,224 properties** with at least one OPEN repair-type violation dated after 2026-07-22 (pulled 2026-10-22; actual violation dates run 2026-07-23 → 2026-10-21).
- **3,463 kept violation rows** — 1,980 STRUCTURAL, 1,483 ENVELOPE — out of 11,425 OPEN rows the city listed for the window. The other 7,962 rows were not kept, for three different reasons: explicit paperwork and housekeeping items (arrange inspection, register vacant building, smoke detectors, weeds, rodents, permits — the 22 most frequent are itemised in the QA report and add up to 2,314 rows); mechanical items (elevators, boilers, wiring — excluded by design); and descriptions the keyword rules do not classify, which include some generic repair wording (REPAIR OR REPLACE, REPAIR FLOOR, REPAIR SCREENS, REPAIR LINTELS). A property whose only open items fall in those groups is not in this list — see [docs/method.md](docs/method.md).
- **Primary category:** 970 properties STRUCTURAL, 254 ENVELOPE. 559 properties have 3 or more open repair items; the maximum on one address is 13.
- **Ranking:** most structural + envelope work first, then total open items, then most recent — the top of the file is the heaviest work.
- **15 columns**, no blanks except `latitude` (1), `longitude` (1) where the city has not geocoded the address.
- **Most common open items:** REPAIR EXTERIOR WALL (441 properties), REPAIR PORCH SYSTEM (261), REPAIR FENCE (210), REPAIR INTERIOR WALLS/CEILING (198), REPAIR EXTERIOR STAIR (197), REPLCE WINDOW PANES, PLEXGLAS (176), MAINTAIN WINDOW (168), REPAIR/REBUILD GARAGE OR SHED (157), CHIMNEY (136), PARAPET (122).
<!-- whats:end -->

## Columns

| Column | Meaning |
|---|---|
| `property_key`, `address`, `city`, `state` | Address as the city records it; `city` = Chicago, `state` = IL |
| `open_work_violation_count` | OPEN repair-type violations at the address inside the window |
| `primary_category` | STRUCTURAL if any structural item is open, otherwise ENVELOPE |
| `structural`, `envelope`, `mechanical` | Count per category (`mechanical` is always 0 in this edition) |
| `violation_types` | Distinct violation descriptions, most frequent first, `;`-separated |
| `earliest_open_date`, `latest_open_date` | First / last violation date among the kept items |
| `latitude`, `longitude` | As published by the city |
| `source_url` | Live city API query for every OPEN violation at this exact address |

Full definitions with examples: [docs/column_dictionary.md](docs/column_dictionary.md).

## How it was built

Built with an AI coding agent (Claude Code) by u/wavezhou. Data: City of Chicago Data Portal dataset [22u3-xenr](https://data.cityofchicago.org/d/22u3-xenr) (Building Violations) via the public SODA API — no scraping, no login, no API key. Kept only violations that mean physical repair work (porch, roof, masonry, windows, doors, fences); dropped paperwork items (register, smoke detectors, weeds). Aggregated to one row per address.

> Built with an AI coding agent (Claude Code); data pulled from the City of Chicago / Cook County open-data APIs; every row links to the original public record; no phone numbers, no emails, no skip tracing.

The exact query URLs, the three classification regexes and the aggregation rules are in [docs/method.md](docs/method.md). The script that turns the raw pull into the files above is [tools/make_free_edition.py](tools/make_free_edition.py) (standard library + openpyxl). The upstream fetch script is not published here; `docs/method.md` has everything needed to reproduce the pull.

## Limitations

- **OPEN status lags compliance.** The city marks a violation closed only after a re-inspection, which can take weeks or months after the work is done. Some listed items are already fixed. Click `source_url` to see what the city shows today.
- **Address-level, not parcel (PIN) level.** One row = one address string as the inspector entered it. A multi-unit building is one row; a corner lot with two addresses can appear twice; there is no owner, PIN or mailing data in this edition.
- **Three-month window.** Only violations dated after the window start (2026-07-22 for the current release) are counted. A property with older violations that are still OPEN is not here unless it also has a newer one.
- **Keyword classification.** STRUCTURAL / ENVELOPE / dropped is decided by regular expressions on the city's `violation_description` text. It is good, not perfect; a few descriptions are ambiguous. The QA report itemises the explicit paperwork drops; `docs/method.md` explains what else is excluded (mechanical items and unclassified descriptions, including some generic repair wording), so you can judge.
- **Counts measure items, not dollars.** 9 open items can be nine small things or one collapsing porch written up nine ways.
- **A moving target.** The city updates the dataset daily. This file is a snapshot and is refreshed on Fridays.

## What this is NOT

No phone numbers, no emails, no skip tracing — in any file here. The Chicago violation files carry no owner names or mailing addresses either; the only names in this repository are the public tax-roll taxpayer names in the Cook County *Estate-of* sample under [data/extras/](data/extras/). Public records only. Nothing here is legal, investment or construction advice.

## Refresh schedule

<!-- refresh:start -->
Every **Friday**. Each refresh replaces the dated CSV/XLSX in `data/`, updates `stats.json` and the QA report, and adds a CHANGELOG entry with the new counts (older files stay in git history). Current data: the pull of Thursday 2026-10-22. **Next refresh: Friday 2026-10-30.**
<!-- refresh:end -->

## Requests

Want another Socrata city or a column added? Open an issue or comment on the Reddit thread — free additions go into [data/extras/](data/extras/). Already there: a 20-row sample of Cook County parcels whose 2026 tax-roll taxpayer reads *Estate of …* ([csv](data/extras/cook_county_estate_of_SAMPLE_20_rows.csv) · [table](data/extras/cook_county_estate_of_SAMPLE_20_rows.md)). Unlike the Chicago files, that sample contains public tax-roll taxpayer / owner names and mailing addresses as the Cook County Assessor publishes them (still no phone numbers, emails or skip tracing); details in [data/extras/README.md](data/extras/README.md).

Questions about OPEN status, PIN vs address, importing into PropStream / BatchLeads / REISift, or mail compliance: [docs/faq.md](docs/faq.md).

## License

Everything in this repository (data files, documents, the build script) is released under **Creative Commons Attribution 4.0 International (CC BY 4.0)** — use it for anything, including commercial work, with attribution. Suggested attribution: *"Chicago Open Building Violations free edition (github.com — chicago-open-violations-leads); data from the City of Chicago Data Portal, dataset 22u3-xenr."* See [LICENSE](LICENSE). The underlying records are public data of the City of Chicago, published under the Data Portal's terms of use; the City is not affiliated with and does not endorse this repository. No warranty of any kind.

Notice required by the City of Chicago Data Portal terms of use: *This site provides applications using data that has been modified for use from its original source, www.cityofchicago.org, the official website of the City of Chicago. The City of Chicago makes no claims as to the content, accuracy, timeliness, or completeness of any of the data provided at this site. The data provided at this site is subject to change at any time. It is understood that the data provided at this site is being used at one’s own risk.*

## Support this work

The free list stays free. Three paid add-ons help pay for the weekly refreshes. They are sold at the
[Open Record Data checkout](https://openrecorddata.vercel.app) — one-time PayPal payment, download links on the next page,
14-day refund if a file won't open or is not as described, newer snapshot free within 30 days.

<!-- SHOP_LINKS -->
- **[Owner-of-record edition — $9](https://openrecorddata.vercel.app/buy/chicago-owner-edition).** The same Chicago list plus PIN, owner of record and mailing address from the Cook County Assessor *where a match was found* (910 of 1,265 properties, 72%; 780 HIGH / 130 MEDIUM confidence), absentee flag, owner type and a county-record link on every matched row; unmatched rows are included as-is. Public tax-roll names only.
- **[Cook County *Estate-of* parcels — $7](https://openrecorddata.vercel.app/buy/cook-estate-of-parcels).** 162 parcels whose 2026 tax-roll taxpayer or owner name reads *Estate of …* (pulled 2026-10-20), with mailing address and HIGH / MEDIUM confidence; the 20-row free sample is in [data/extras/](data/extras/).
- **[Socrata Lead Puller kit — $12](https://openrecorddata.vercel.app/buy/socrata-lead-puller-kit).** Run the same pull for Chicago, Austin, Cincinnati or any other Socrata city in your browser, with editable keyword rules — no code.
- **[All three — $19](https://openrecorddata.vercel.app/buy/bundle).**

All three are public records only — no phone numbers, no emails, no skip tracing. Support: open an issue here, or reply to your PayPal receipt email.
