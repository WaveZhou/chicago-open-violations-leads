# FAQ

Built with an AI coding agent (Claude Code); data pulled from the City of Chicago / Cook County open-data APIs; every row links to the original public record; no phone numbers, no emails, no skip tracing.

## Why only OPEN violations?

Because OPEN is the city's own signal that work is still owed. A violation goes OPEN when the inspector writes it up and is closed (status `COMPLIED`, `NO ENTRY`, etc.) only after a re-inspection. For a mailer or a bid list, OPEN is the closest thing to "this building needs work right now" that exists in public data.

The catch is lag: the city closes items only after someone re-inspects, which can be weeks or months after the owner fixed the problem. So some rows describe work that is already done. Treat the list as "flagged by the city, not yet cleared", and click `source_url` on any address you are about to spend money on — it shows what the city lists today.

## Why address-level and not PIN (parcel) level?

The violations dataset records the address the inspector entered; it does not carry the Cook County PIN. Matching addresses to PINs needs a second source (the Cook County Assessor's parcel-address file), address normalisation, and handling of one-address-many-PINs cases (condo buildings) and many-addresses-one-PIN cases (corner lots). On a 40-address random probe the exact address-to-PIN hit rate was about 60%, with another 15% needing a fuzzy fallback.

The free edition stays at the address level so that every number in it is traceable to a single city record with no matching step in between. The paid owner-of-record edition adds the PIN and the Assessor's taxpayer / mailing address *where a match was found*, with a confidence flag and a second link to the county record for each row; unmatched rows are delivered as-is.

## How do I import this into PropStream / BatchLeads / REISift?

All three accept a CSV list of property addresses and match it against their own ownership data. The general recipe:

1. Open the CSV (or the `Properties` sheet of the XLSX) and keep the columns `address`, `city`, `state` — optionally `open_work_violation_count`, `primary_category` and `violation_types` as custom/tag fields so you can segment later.
2. Save as CSV.
3. In the tool, use its list-import function (PropStream: *My Properties → Import*; BatchLeads: *Lists → Import*; REISift: *Records → Import*) and map `address` → Street/Address, `city` → City, `state` → State.
4. Let the tool run its owner / skip-trace match. That step happens inside the product you already pay for; nothing in this repository does it.

Two caveats. **There is no ZIP column** because the city dataset does not publish one; most importers accept street + city + state, but if yours requires ZIP, run the file through a ZIP lookup / geocoder first (latitude and longitude are included to make that easy). **Addresses are the inspector's string**, so a few contain unit or range notation; the tools usually cope, but check the unmatched rows after import.

## Can you do my city?

If your city publishes code-violation data on a Socrata portal (addresses ending in `/resource/xxxx-xxxx.json`), yes — the method in [`docs/method.md`](method.md) works with a different dataset id, field names and keyword list. Open an issue with the city name and the dataset link, or comment on the Reddit thread; useful additions go into `data/extras/` for free. A browser-based tool that runs the same pull for any Socrata city with editable keyword rules is one of the paid add-ons linked at the bottom of the README.

Cities that use ArcGIS Hub, Accela, or a PDF-only portal need a different approach and are not covered.

## Is this legal to use for mail?

This is not legal advice; here is what is factual.

- The source is public data the City of Chicago publishes for anyone to use under its Data Portal terms of use. This repository adds filtering and formatting; it does not add any personal data.
- The Chicago violation files contain property addresses and inspection facts only — no names, phone numbers, emails or owner mailing addresses. There is nothing in them that a phone-marketing (TCPA) or email (CAN-SPAM) rule attaches to.
- Mailing a letter to "Owner / Current Resident" at a property address is ordinary direct mail. Follow the usual rules: honour anyone who asks you to stop, do not misrepresent who you are or imply the city sent the letter, and comply with Illinois and local consumer-protection and real-estate advertising rules (and your state's rules if you are not in Illinois).
- If you append owner names or mailing addresses from another source, you take on that source's terms and the obligations that come with personal data. The free edition keeps you on the property-only side of that line on purpose. (The 20-row Cook County *Estate-of* sample in `data/extras/` is such a source — public tax-roll taxpayer names and mailing addresses; see [data/extras/README.md](../data/extras/README.md).)

## What counts as a "repair-type" violation? Why are smoke detectors / weeds / permits missing?

The list keeps violations that mean physical construction work on the building: porch, roof, masonry, foundation, stairs, parapet, chimney, garage, windows, doors, siding, gutters, fences, plaster, ceilings. It drops paperwork items (arrange inspection, register vacant building, permits, owner-or-contractor notices), housekeeping items (weeds, rodents, nuisance, graffiti) and life-safety devices (smoke / CO detectors) — not because they do not matter, but because they do not indicate a rehab-size job. Mechanical items (elevators, boilers, plumbing, wiring) are recognised but excluded from the free edition, and descriptions that match no rule at all — including some generic repair wording such as REPAIR OR REPLACE or REPAIR SCREENS — are dropped too. The exact rules are the regular expressions in [`docs/method.md`](method.md); the most frequent paperwork drops are itemised in the QA report in `data/` (`QA_REPORT_<window-start>.txt`), the other two groups are not.

## Why is the count different from what I see on the city's portal?

Three reasons, in order of size: (1) the portal shows all OPEN violations, the list keeps repair-type ones only — about 30% of the raw rows; (2) the list covers violations dated after the window start (about three months back; 2026-07-22 for the current release), the portal has everything; (3) the portal updates daily, the list is a snapshot refreshed on Fridays. The row's `source_url` shows the live, unfiltered OPEN record for that address so you can see the difference yourself.

## How often is it refreshed, and will old files disappear?

Every Friday. The dated CSV/XLSX in `data/` are replaced, `stats.json` and the QA report are regenerated, and `CHANGELOG.md` gets a new entry with the counts. Older files remain in the git history.

## Is there a version with owner names?

Not for the Chicago list, by design. A paid owner-of-record edition (Cook County Assessor match where found, with confidence flags and county links) and a Cook County *Estate-of* parcel list are linked at the bottom of the [README](../README.md). Both are public tax-roll records only — still no phone numbers, emails or skip tracing. The only names inside this repository are in the free 20-row *Estate-of* sample under `data/extras/` (public tax-roll taxpayer names and mailing addresses; see [data/extras/README.md](../data/extras/README.md)).
