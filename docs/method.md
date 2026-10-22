# Method — how the list is pulled, classified and aggregated

This page has everything needed to reproduce the free edition by hand or in any language. It deliberately does not include the complete fetch script; the second-stage script that builds the CSV/XLSX/sample from the raw pull is in [`tools/make_free_edition.py`](../tools/make_free_edition.py).

Built with an AI coding agent (Claude Code); data pulled from the City of Chicago / Cook County open-data APIs; every row links to the original public record; no phone numbers, no emails, no skip tracing.

## 1. Source

- **Dataset:** City of Chicago Data Portal, *Building Violations*, id `22u3-xenr` — <https://data.cityofchicago.org/d/22u3-xenr>
- **Access:** the public Socrata Open Data API (SODA 2.x), JSON endpoint `https://data.cityofchicago.org/resource/22u3-xenr.json`. No login, no scraping, no API key (anonymous calls are throttled; an app token raises the limit but is not required).
- **Fields used:** `id, violation_date, violation_status, violation_status_date, violation_code, violation_description, violation_location, inspection_category, department_bureau, address, street_number, street_direction, street_name, street_type, property_group, latitude, longitude`.
- **Pull date for this release:** 2026-10-13. **Window:** `violation_date > 2026-07-13` (about three months).

## 2. SoQL queries

### 2a. The raw pull (paged, 50,000 rows per page)

Readable form:

```
https://data.cityofchicago.org/resource/22u3-xenr.json
  ?$select=id,violation_date,violation_status_date,violation_code,violation_description,
           violation_location,inspection_category,department_bureau,address,street_number,
           street_direction,street_name,street_type,property_group,latitude,longitude
  &$where=violation_status='OPEN' AND violation_date > '2026-07-13T00:00:00'
  &$order=violation_date DESC
  &$limit=50000
  &$offset=0
```

URL-encoded, ready to paste into a browser (first page):

```
https://data.cityofchicago.org/resource/22u3-xenr.json?%24select=id%2Cviolation_date%2Cviolation_status_date%2Cviolation_code%2Cviolation_description%2Cviolation_location%2Cinspection_category%2Cdepartment_bureau%2Caddress%2Cstreet_number%2Cstreet_direction%2Cstreet_name%2Cstreet_type%2Cproperty_group%2Clatitude%2Clongitude&%24where=violation_status%3D%27OPEN%27%20AND%20violation_date%20%3E%20%272026-07-13T00%3A00%3A00%27&%24order=violation_date%20DESC&%24limit=50000&%24offset=0
```

Increase `$offset` by the number of rows returned until a page comes back short. For this release the whole window fit in one page: **11,650 raw OPEN rows**. Each request is retried up to 5 times with a growing pause on 5xx / throttle errors.

### 2b. Sanity count (no download)

```
https://data.cityofchicago.org/resource/22u3-xenr.json?$select=count(*)&$where=violation_status='OPEN' AND violation_date > '2026-07-13T00:00:00'
```

The number moves daily as the city adds and closes violations, so it will not equal 11,650 for long.

### 2c. The per-row `source_url` (one-click verification)

Every row carries a query that returns every OPEN violation the city currently lists at that exact address, newest first:

```
https://data.cityofchicago.org/resource/22u3-xenr.json
  ?$select=address,violation_date,violation_code,violation_description,violation_status
  &$where=violation_status='OPEN' AND address='4725 S MICHIGAN AVE'
  &$order=violation_date DESC
  &$limit=200
```

Note that `source_url` is **not** limited to the three-month window, so it may show more rows than `open_work_violation_count` — that is intended: it shows the whole live record for the address.

## 3. Classification — the regexes, verbatim

Every raw row's `violation_description` is upper-cased, trimmed, and tested in this order. The first rule that fires wins.

1. Blank, or exactly `UNDEFINED`, `OPEN`, `REPLACE`, `SEE INSPECTOR COMMENTS` → **OTHER, dropped**.
2. Matches `ADMIN` → **dropped** (even if a construction keyword also appears).
3. Matches `STRUCTURAL` → **kept, category STRUCTURAL**.
4. Matches `ENVELOPE` → **kept, category ENVELOPE**.
5. Matches `MECHANICAL` → category MECHANICAL, **not kept in this edition** (the fetch has an `--include-mechanical` switch that the free edition does not use).
6. Anything else → **OTHER, dropped**.

The three patterns that decide what you see (Python `re`, case-insensitive):

```python
STRUCTURAL = re.compile(
    r"\b(PORCH|EXTERIOR WALL|EXTERIOR STAIR|INTERIOR STAIR|\bSTAIR|PARAPET|CHIMNEY|"
    r"GARAGE|SHED|FOUNDATION|LINTEL|MASONRY|BRICK|EAVES|CORNICE|CANOPY|BALCON|"
    r"FLOOR SYSTEM|JOIST|BEAM|COLUMN|LOAD|ROOF|FIRE ESCAPE|RETAINING WALL|"
    r"PORCH SYSTEM|REBUILD)\b", re.I)

ENVELOPE = re.compile(
    r"\b(WINDOW|WINDOW PANE|PLEXGLAS|EXTERIOR DOOR|SCREEN|SIDING|GUTTER|DOWNSPOUT|"
    r"FLASHING|WEATHER|DOOR HARDWARE|FENCE|PLASTER|INTERIOR WALLS|CEILING|"
    r"STUCCO|SOFFIT|TUCKPOINT)\b", re.I)

# Explicit paperwork / non-construction items to exclude even if a keyword leaks
ADMIN = re.compile(
    r"ARRANGE (PREMISE|FOR REINSPECT)|PREMISE INSPECTION|REGISTER|REGISTRATION|"
    r"SMOKE DETECT|CARBON MONOX|HIGH WEEDS|CUT OR REMOVE|RODENT|NUISANCE|"
    r"POST (SIGN|ADDRESS)|SEE INSPECTOR|OWNER OR LICENSED CONTRACTOR|"
    r"PLANS & PERMITS|PERMIT REQ|WORK NOT ALLOWED|FILE|AFFIDAVIT|"
    r"LICENSE|VACANT BUILDING REG|SCAVENGER|GRAFFITI", re.I)
```

The fourth pattern, recognised but excluded from the free edition:

```python
MECHANICAL = re.compile(
    r"\b(ELEVA|BOILER|FURNACE|HVAC|PLUMB|ELECTRIC(AL)? SERVICE|WIRING|"
    r"WATER HEATER|HEATING PLANT|VENTIL)\b", re.I)
```

Known quirks, kept as-is so the published counts are reproducible: the whole alternation is wrapped in `\b…\b`, so truncated stems such as `BALCON`, `ELEVA`, `VENTIL`, `PLUMB` only match when they are a complete word — `BALCONY` or `PLUMBING` do not fire those branches (`PLUMBING` is still dropped because it never matches STRUCTURAL/ENVELOPE). `REPLACE` on its own is dropped in step 1 because the city uses it as a bare placeholder. Plural forms are not matched either: `REPAIR SCREENS`, `REPAIR LINTELS`, `GUTTERS`, `WINDOWS` do not fire the singular branches, and generic wording such as `REPAIR OR REPLACE`, `REPAIR FLOOR` or `BUILDING IN DISREPAIR` matches nothing — together a few hundred genuine repair rows per quarter end up unclassified and dropped, so the kept set under-counts repair work rather than over-counting it. If you change the patterns, re-check the dropped list in the QA report.

For this release the split was: 3,518 kept rows (1,998 STRUCTURAL, 1,520 ENVELOPE); 8,132 dropped. The 22 most frequent **explicitly-dropped (ADMIN)** descriptions are listed in `data/QA_REPORT_2026-07-13.txt` and account for 2,349 of the 8,132 dropped rows; the remainder are MECHANICAL matches (mostly `MAINTAIN OR REPAIR ELECT/HYDRO ELEVA`) and descriptions that match no pattern at all, which are not itemised in that report — the top five are ARRANGE PREMISE INSPECTION (869), STOP/REMOVE NUISANCE (233), ARRANGE FOR REINSPECTION REGAR (201), PLANS & PERMITS REQ - CONTRCTR (181), INSTALL SMOKE DETECTORS (164).

## 4. Aggregation — one row per address

- **Key:** the dataset's own `address` field, whitespace-collapsed and upper-cased. It is already canonical (`6738 S RHODES AVE`), so no suffix normalisation is applied. If `address` is blank the key is built from `street_number + street_direction + street_name + street_type`. The same key is what `source_url` filters on.
- **Per address, over the kept rows:**
  - `open_work_violation_count` = number of kept rows.
  - `structural`, `envelope`, `mechanical` = kept rows per category (`mechanical` is 0 in this edition).
  - `primary_category` = STRUCTURAL if `structural > 0`, else ENVELOPE (else MECHANICAL / OTHER — never happens here).
  - `violation_types` = distinct `violation_description` values ordered by how many times they occur at the address, joined with `;`, cut at 600 characters.
  - `earliest_open_date`, `latest_open_date` = min / max `violation_date` (date part only).
  - `latitude`, `longitude` = taken from the first kept row seen for the address (rows arrive newest first).
  - `source_url` = the 2c query with the key substituted (single quotes doubled for SoQL).
- **Dropped from the free edition:** `violation_codes` (sorted distinct codes, `;`-joined) and `property_group` (city building-group id). The paid editions keep them.

## 5. Ranking

Rows are sorted descending by `(structural + envelope, open_work_violation_count, latest_open_date)` — most repair work first, then the most items, then the most recent. The top of the file is therefore the heaviest work, not the newest.

## 6. Free-edition packaging

`tools/make_free_edition.py --full <FULL.csv> --qa <QA_REPORT.txt> --pull-date 2026-10-13 --docs` reads the 17-column FULL file and writes:

- `data/chicago_open_violations_FREE_<date>.csv` — 15 columns, UTF-8 with BOM.
- `data/chicago_open_violations_FREE_<date>.xlsx` — `Properties` (frozen header, autofilter, `source_url` as a *city record* hyperlink, real date cells), `README`, `Column_Dictionary`, `Stats`.
- `data/SAMPLE_25_rows.md` — the 25 addresses with the most open items (ties: more structural, then more recent).
- `data/stats.json`, `data/CHANGELOG.md`, `docs/column_dictionary.md` — all counts measured from the file, not estimated.

## 7. Checking a row yourself

1. Open the row's `source_url` in a browser. You get JSON: one object per OPEN violation at that address, newest first.
2. Compare `address` in the JSON with the row — they must be identical strings.
3. Count the objects whose `violation_date` is after the window start and whose description matches the kept categories; that should equal `open_work_violation_count`. Objects outside the window or with paperwork descriptions explain any difference.
4. For a human-readable page, search the address on <https://webapps1.chicago.gov/buildingrecords/> (the city's Building Violations lookup) — this needs a manual search, which is why the file links to the API instead.
