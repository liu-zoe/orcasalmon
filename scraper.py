### Script Name: scraper.py
# Purpose: Download this year's salmon and orca data for the dashboard
# Author: Zoe Liu
# Date: Oct 12th 2022
# Updated: May 17th 2026 — Acartia SRKW detection for the Mar 7 2026 schema change
# Updated: Nov 24th 2026 — every salmon source downloads itself (no browser /
#   Selenium needed); see orcasalmon/salmon.py
#
# Run from anywhere:  python scraper.py
# Then look over the changed files in data/ and commit the ones you want.

from orcasalmon.acartia import proc_acartia, scrape_acartia
from orcasalmon.config import CURYR
from orcasalmon.salmon import SALMON_SOURCES

# 1. Salmon: download this year's data for every source that can download
#    itself. Lake Washington is saved by hand (see data/lakewash/README.md).
for source in SALMON_SOURCES:
    if source.can_download:
        print(f"Downloading {source.label} {CURYR} ...")
        source.download(CURYR)
    else:
        print(f"Skipping {source.label}: no automatic download")

# To download the full history of one source (run once, e.g. for a new source):
#   from orcasalmon.salmon import albion_chum
#   for y in range(1988, CURYR + 1):
#       albion_chum.download(y)

# 2. Orcas: download the Acartia feed and tag Southern Resident reports.
#    Writes data/acartia/srkw_<year>.csv with confirmed and candidate rows.
scrape_acartia()
proc_acartia()
