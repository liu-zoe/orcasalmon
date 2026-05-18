### Script Name: scraper.py
# Purpose: Scraping chinook data and orca data for dashboard
# Author: Zoe Liu

# Date: Oct 12th 2022
# Updated: May 17th 2026 — proc_acartia SRKW detection updated to handle the
#   Acartia source schema change of Mar 7 2026 (ecotype info moved out of the
#   `type` field into comments). See scrapefunc.py docstring for details.

#### 1 Setup
# 1.1 Import libraries
from datetime import date
import pandas as pd
pd.options.mode.chained_assignment = None  # suppress chained assignment
from scrapefunc import (scrape_fos, scrape_bon, scrape_acartia, proc_acartia)

# 1.2 Get today's date
today = date.today()
todaystr = str(today)
curyr = today.year
lastyr = curyr - 1
twoyr = curyr - 2
ayl = [y for y in range(1980, curyr + 1)]  # year list for Albion
byl = [y for y in range(1939, curyr + 1)]  # year list for Bonneville Dam

# 1.3 Define data path
fos_path = './data/foschinook/'
bon_path = './data/bonchinook/'
acartia_path = './data/acartia/'

##### 2 Scrape web data
# 2.1 Scrape Bonneville Dam Chinook Daily count

# Use the following line to download the current year
scrape_bon(yrs=str(curyr), bon_path=bon_path)

# Use the following lines to download all fos chinook data
# Note: commented out after running it once
'''
for y in byl:
  scrape_bon(yrs=str(y), bon_path=bon_path)
'''

# 2.2 Scrape Chinook data by year

# Use the following line to download the current year
scrape_fos(yrs=str(curyr), spe='CHINOOK SALMON')

# Use the following lines to download all fos chinook data
# Note: commented out after running it once
'''
for y in ayl:
  scrape_fos(yrs=str(y), spe='CHINOOK SALMON', fos_path=fos_path)
'''

# 2.3 Scrape Acartia orca data
# Run the following code to scrape Acartia data
scrape_acartia(acartia_path=acartia_path)

# Processing Acartia Data
# Writes data/acartia/srkw_<year>.csv with both confirmed and candidate SRKW.
# The existing dashboard filter `srkw==1` still surfaces only high-confidence
# detections; rows where srkw_candidate==1 are now also present in the file but
# remain hidden until the dashboard filter is updated to include them.
proc_acartia(acartia_path)
