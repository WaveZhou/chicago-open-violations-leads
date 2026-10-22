# data/extras — free additions

Free extras that pair with the Chicago list or that readers asked for. Everything here is CC BY 4.0 like the rest of the repository (see [LICENSE](../../LICENSE)).

## Cook County *Estate-of* taxpayer parcels — 20-row sample

| File | What it is |
|---|---|
| [cook_county_estate_of_SAMPLE_20_rows.csv](cook_county_estate_of_SAMPLE_20_rows.csv) | 20 parcels × 19 columns, UTF-8 with BOM. Open it with the `pin` column as **text** — PINs are 14-digit strings and 3 of the 20 start with a zero |
| [cook_county_estate_of_SAMPLE_20_rows.md](cook_county_estate_of_SAMPLE_20_rows.md) | The same 20 parcels as a 6-column markdown table (PIN, property address, municipality, class group, confidence, mailing city/state) |

**Read this before you use it.** Unlike the Chicago violation files in `data/`, this sample is a list of **taxpayers, not just properties**: it carries `taxpayer_name`, `owner_name` and the mailing address (`mailing_address`, `mailing_city`, `mailing_state`, `mailing_zip`) exactly as the Cook County Assessor publishes them in its public parcel-address file (dataset 3723-97qp) — the *Estate of …* wording in the taxpayer name is the whole point of the list. Still no phone numbers, no emails, no skip tracing; every row links to the county record in `source_url`.

Sample rules: residential (class 2xx), not sold since 2025-01-01, HIGH confidence first, one per surname, at most two per municipality. The full list at the 2026-10-20 pull is 162 parcels (40 HIGH / 122 MEDIUM); the county republished its roll on 2026-10-15, so this sample supersedes the one taken on 2026-10-13. It is a floor, not a census: the county changes a taxpayer name to *Estate of* only when it is notified. The full list is a paid add-on linked at the bottom of the [repository README](../../README.md).

Use it for respectful, compliant direct mail only, and follow the applicable Illinois probate and marketing rules.

Sources: Cook County Assessor open data — 3723-97qp (Parcel Addresses: taxpayer + owner names and mailing address), pabr-t5kh (Parcel Universe: class, township, municipality), wvhk-k5uv (Parcel Sales since 2025-01-01).

Built with an AI coding agent (Claude Code); data pulled from the City of Chicago / Cook County open-data APIs; every row links to the original public record; no phone numbers, no emails, no skip tracing.
