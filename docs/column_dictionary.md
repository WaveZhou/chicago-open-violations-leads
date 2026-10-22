# Column dictionary -- FREE edition (15 columns)

One row per property (address). Release 2026-10-13, 1,265 rows. Examples come from the first row of the file.

| # | Column | Type | Description | Example |
|---:|---|---|---|---|
| 1 | `property_key` | text | Upper-cased canonical address used to group violations into one row per property; in practice identical to the city's `address` field. | 4725 S MICHIGAN AVE |
| 2 | `address` | text | Street address exactly as it appears in the City of Chicago Building Violations dataset. | 4725 S MICHIGAN AVE |
| 3 | `city` | text | Always 'Chicago'. | Chicago |
| 4 | `state` | text | Always 'IL'. | IL |
| 5 | `open_work_violation_count` | integer | Number of OPEN violations at this address, dated inside the pull window, that require physical repair work (structural + envelope). Paperwork-only items are excluded. | 13 |
| 6 | `primary_category` | text | Worst category present at the address: STRUCTURAL if at least one structural item is open, otherwise ENVELOPE. | STRUCTURAL |
| 7 | `structural` | integer | Count of OPEN structural items (porch, roof, masonry, foundation, stairs, parapet, chimney, garage, lintel, joist, fire escape ...). | 6 |
| 8 | `envelope` | integer | Count of OPEN exterior-envelope / finish items (windows, exterior doors, siding, gutters, downspouts, fences, plaster, ceilings, tuckpointing ...). | 7 |
| 9 | `mechanical` | integer | Count of OPEN mechanical items (boiler, elevator, plumbing, wiring). Always 0 in this edition because mechanical items are not kept. | 0 |
| 10 | `violation_types` | text | Distinct violation descriptions at the address, most frequent first, separated by ';'. Truncated at 600 characters. | REPLCE WINDOW PANES, PLEXGLAS;PARAPET & COPING;REPAIR INTERIOR STAIR SYSTEM;REPAIR EXTE... |
| 11 | `earliest_open_date` | date | Earliest violation_date among the kept OPEN items at this address (YYYY-MM-DD). | 2026-09-09 |
| 12 | `latest_open_date` | date | Latest violation_date among the kept OPEN items at this address (YYYY-MM-DD). | 2026-09-10 |
| 13 | `latitude` | decimal | Latitude as published by the city; blank for a few addresses the city has not geocoded. | 41.808520059 |
| 14 | `longitude` | decimal | Longitude as published by the city; blank for a few addresses the city has not geocoded. | -87.6226693307 |
| 15 | `source_url` | url | Live SODA API query that returns every OPEN violation the city currently lists at this exact address. Open it in a browser to verify the row against the original public record. | `https://data.cityofchicago.org/resource/22u3-xenr.json?%24se...` |

## Columns removed from the FULL build

| Column | Why it is not in the free edition |
|---|---|
| `violation_codes` | City violation code list (e.g. `CN061014;CN065034`). Redundant with `violation_types` for outreach use. |
| `property_group` | City's internal building-group id. Not useful without the city's own join tables. |

## Notes

- Blank cells in this release: `latitude` 1, `longitude` 1 (all other columns 0).
- `mechanical` is always 0 in the free edition; the column is kept so the layout matches the paid editions.
- Dates are ISO `YYYY-MM-DD` text in the CSV and real date cells in the XLSX.
- `source_url` in the XLSX shows the text *city record* and carries the URL as a hyperlink; the CSV has the raw URL.
