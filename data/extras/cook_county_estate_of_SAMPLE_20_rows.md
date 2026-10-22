**Sample: 20 Cook County parcels where the 2026 tax roll lists the taxpayer or owner as 'Estate of ...'** -- full list 162 parcels (40 HIGH / 122 MEDIUM confidence), pulled 2026-10-20. Sample = residential, not sold since 2025-01-01, HIGH first, one per surname, max two per municipality.

| PIN | Property address | Municipality | Class group | Confidence | Mailing city/state |
|---|---|---|---|---|---|
| 02363070400000 | 3711 MEADOW DR | CITY OF ROLLING MEADOWS | Residential (6 units or less) | HIGH | PALATINE, IL |
| 03031000541219 | 1022 FERNDALE CT B1 | VILLAGE OF WHEELING | Residential (6 units or less) | HIGH | DEERFIELD, IL |
| 11301190270000 | 1105 DOBSON ST | CITY OF EVANSTON | Residential (6 units or less) | HIGH | EVANSTON, IL |
| 14084030281023 | 5100 N MARINE DR 4K | CITY OF CHICAGO | Residential (6 units or less) | HIGH | CHICAGO, IL |
| 14163000321263 | 4343 N CLARENDON AVE 1611 | CITY OF CHICAGO | Residential (6 units or less) | HIGH | CHICAGO, IL |
| 31153160020000 | 4605 BLARNEY DR | VILLAGE OF MATTESON | Residential (6 units or less) | HIGH | JOLIET, IL |
| 32292130130000 | 15 23RD ST | CITY OF CHICAGO HEIGHTS | Residential (6 units or less) | HIGH | POSEN, IL |
| 32294160520000 | 233 28TH PL | VILLAGE OF SOUTH CHICAGO HEIGHTS | Residential (6 units or less) | HIGH | SMYRNA, GA |
| 08221040111099 | 2755 EMBERS LN A | VILLAGE OF ARLINGTON HEIGHTS | Residential (6 units or less) | MEDIUM | BRADENTON, FL |
| 10104070430000 | 9831 KEELER AVE | VILLAGE OF SKOKIE | Residential (6 units or less) | MEDIUM | SKOKIE, IL |
| 10152120580000 | 9518 N KARLOV AVE | VILLAGE OF SKOKIE | Residential (6 units or less) | MEDIUM | HOUSTON, TX |
| 10263150130000 | 3841 W CHASE AVE | VILLAGE OF LINCOLNWOOD | Residential (6 units or less) | MEDIUM | LISLE, IL |
| 12022000200000 | 1225 S CUMBERLAND AVE | CITY OF PARK RIDGE | Residential (6 units or less) | MEDIUM | PLAINFIELD, IL |
| 12041030330000 | 6317 KIRSCHOFF RD | VILLAGE OF ROSEMONT | Residential (6 units or less) | MEDIUM | VOLO, IL |
| 12133060300000 | 4228 N OVERHILL AVE | VILLAGE OF NORRIDGE | Residential (6 units or less) | MEDIUM | NORRIDGE, IL |
| 13184010250000 | 6732 W SENIOR PL | VILLAGE OF HARWOOD HEIGHTS | Residential (6 units or less) | MEDIUM | HARWOOD HEIGHTS, IL |
| 15083020460000 | 740 N ROHDE AVE | VILLAGE OF HILLSIDE | Residential (6 units or less) | MEDIUM | HILLSIDE, IL |
| 15103290040000 | 811 S 20TH AVE | VILLAGE OF MAYWOOD | Residential (6 units or less) | MEDIUM | MAYWOOD, IL |
| 15161100320000 | 3501 ADAMS ST HSE | VILLAGE OF BELLWOOD | Residential (6 units or less) | MEDIUM | WALDORF, MD |
| 15174010030000 | 21 ORCHARD ST | VILLAGE OF HILLSIDE | Residential (6 units or less) | MEDIUM | HILLSIDE, IL |

Class group = Cook County Assessor major class: 1xx Vacant land; 2xx Residential (6 units or less); 3xx Multi-family 7+; 5xx Commercial/Industrial; Exx Exempt.

Sources: Cook County Assessor open data -- 3723-97qp (Parcel Addresses: taxpayer + owner names), pabr-t5kh (Parcel Universe: class, township, municipality), wvhk-k5uv (Parcel Sales since 2025-01-01). Confidence HIGH = both taxpayer and owner name read 'Estate of'; MEDIUM = one of them, or an executor / administrator name. This is a floor, not a census: the county changes a taxpayer name to Estate of only when notified. PINs are 14-digit strings -- open the CSV with the PIN column as text or the leading zero is lost. Built with an AI coding agent (Claude Code); data pulled from the City of Chicago / Cook County open-data APIs; every row links to the original public record; no phone numbers, no emails, no skip tracing.
