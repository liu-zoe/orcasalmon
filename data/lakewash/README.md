# Lake Washington Chinook counts: data sources

Daily counts of adult Chinook salmon passing the Hiram M. Chittenden (Ballard) Locks in Seattle. WDFW and the Muckleshoot Indian Tribe count the fish cooperatively.

**Source page:** [WDFW Lake Washington salmon counts](https://wdfw.wa.gov/fishing/reports/counts/lake-washington), in the "Daily Chinook counts" section.

WDFW's page shows **only the current season**, and WDFW publishes no download or archive for earlier years. Past seasons were therefore copied from [Wayback Machine](https://web.archive.org/) snapshots of that page, taken after each season ended.

## Sources by year

| Year | File | Source | Days | Dates | Sum of daily counts | WDFW season total |
|---|---|---|---|---|---|---|
| 2020 | `2020.csv` | [Wayback 2020-11-12](https://web.archive.org/web/20201112015837/https://wdfw.wa.gov/fishing/reports/counts/lake-washington#chinook) | 56 | 7/24–9/17 | 12,779 | 12,778 |
| 2021 | `2021.csv` | [Wayback 2021-12-02](https://web.archive.org/web/20211202093244/https://wdfw.wa.gov/fishing/reports/counts/lake-washington#chinook) | 85 | 7/8–9/30 | 14,229 | 14,229 |
| 2022 | `2022.csv` | [Wayback 2022-12-04](https://web.archive.org/web/20221204050354/https://wdfw.wa.gov/fishing/reports/counts/lake-washington#chinook) | 87 | 7/8–10/2 | 17,245 | 17,441 |
| 2023 | `2023.csv` | [Wayback 2023-12-05](https://web.archive.org/web/20231205183339/https://wdfw.wa.gov/fishing/reports/counts/lake-washington#chinook) | 95 | 6/30–10/2 | 23,324 | 23,322 |
| 2024 | `2024.csv` | Copied from the live WDFW page and added on 2025-01-18 (commit `e666b0a`). Checked against [Wayback 2024-12-04](https://web.archive.org/web/20241204165029/https://wdfw.wa.gov/fishing/reports/counts/lake-washington#chinook): all 95 rows match. | 95 | 6/30–10/2 | 18,566 | 18,717 |
| 2025 | `2025.csv` | [Wayback 2025-10-10](https://web.archive.org/web/20251010034418/https://wdfw.wa.gov/fishing/reports/counts/lake-washington#chinook) | 95 | 6/30–10/2 | 18,754 | 18,754 |
| 2026 | `2026.csv` | Live WDFW page, copied on 2026-11-24. Marked preliminary by WDFW. | 95 | 6/30–10/2 | 14,675 | 14,675 |

"WDFW season total" is the last running total in WDFW's table. "Sum of daily counts" is what the dashboard plots.

## File format

Each file has the same three columns as WDFW's table:

```
"Date","Daily Count","Running Total"
"6/30",2,2
"7/1",0,2
```

- `Date` is `M/D` with no year; the year comes from the file name.
- Values are copied exactly as published. Running totals were **not** recalculated, so mismatches in WDFW's tables are kept.
- `apputils.load_wash()` reads every `YYYY.csv` in this folder.

## Changes made while copying

- **Date-range rows.** WDFW's first row is often a range, such as "6/18 - 6/30". It is saved under its end date (`6/30` or `7/8`) with the published count. Year suffixes such as "/24" were dropped.
- **2020 starting row.** WDFW's 2020 table starts on 7/25, and that day's running total is already 457. The first 443 fish have no daily breakdown, so they are saved as one row, `"7/24",443,443`, standing in for "season start to 7/24". An August 2020 snapshot (2020-08-14) was checked, but it has no tables. The 2020 table also ends on 9/17.

## Known inconsistencies in WDFW's tables

On some days, WDFW's running total does not equal the previous total plus that day's count. These mismatches are in WDFW's published tables, not copying errors.

- **All years:** scattered ±1 differences, probably rounding in the expanded daily estimates.
- **2022:** on 8/6 and 8/7 the running total is off by −100 and then +100, which cancel. On 8/12 it jumps 201 more than the daily count. This is most of the gap between the daily sum (17,245) and the season total (17,441).
- **2023:** the 9/25 running total was not updated, and 9/26 catches up by 15. The season totals differ by 2.
- **2024:** the running total jumps more than the daily count on 7/14 (+1), 8/14 (+100) and 8/15 (+50). That is the whole 151-fish gap between 18,566 and 18,717. Search results attribute the 18,717 total to a WDFW/Muckleshoot 2024 factsheet.

## Adding a new year

After a season ends (WDFW's table usually runs to about 10/2), save that season's "Daily Chinook counts" table as `YYYY.csv`, using the format above. Then add a row to the table in this file. If the season has already rolled off the live page, use a Wayback Machine snapshot: open `https://web.archive.org/web/*/https://wdfw.wa.gov/fishing/reports/counts/lake-washington` and pick a date between mid-October and the following June.
